"""Tests for multi-fit HDF5, contributor permissions, and APIs."""

from __future__ import annotations

import os
import tempfile
import uuid

import numpy as np
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from analysis.auxil.multi_fit_hdf5 import (
    append_fit,
    get_best_fit_id,
    list_fits,
    remove_fit,
    set_best_fit,
    write_multi_fit_v2,
)
from analysis.auxil.rv_hdf5 import write_rv_curve_v2
from analysis.categories import AnalysisCategory
from analysis.models import Analysis, AnalysisFit
from analysis.services.fit_contribution import contribute_fit, reingest_best_fit_parameters
from analysis.services.fit_permissions import (
    user_can_delete_fit,
    user_can_set_best_fit,
)
from analysis.services.multi_fit_migration import _measurements_from_hdf5_path
from analysis.services.fit_sync import sync_fits_from_hdf5
from stars.models import Project, Star


class MultiFitHdf5Tests(TestCase):
    def test_append_fit_sets_contributor_attrs(self):
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
            path = tmp.name
        measurements = {
            'time': np.array([1.0, 2.0]),
            'rv': np.array([10.0, 11.0]),
        }
        write_rv_curve_v2(path, measurements=measurements, fits=[{
            'id': 'fit-a',
            'label': 'A',
            'is_best_fit': True,
            'parameters': {'K': (100.0, 1.0, 1.0, 'km/s')},
        }])
        fit_id = append_fit(
            path,
            {'label': 'B', 'parameters': {'K': (90.0, 2.0, 2.0, 'km/s')}},
            uploaded_by_user_id=42,
            uploaded_by_username='alice',
        )
        from analysis.auxil.fileio import read2dict
        data = read2dict(path)
        fits = list_fits(data, category='rv_curve')
        self.assertEqual(len(fits), 2)
        contributed = next(f for f in fits if f['id'] == fit_id)
        self.assertEqual(contributed['uploaded_by_user_id'], 42)
        self.assertEqual(contributed['uploaded_by_username'], 'alice')
        os.unlink(path)

    def test_set_best_fit(self):
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
            path = tmp.name
        write_multi_fit_v2(
            path,
            category='spectral_fit',
            hdf5_type='XF',
            fits=[
                {'id': 'a', 'label': 'A', 'is_best_fit': True, 'parameters': {'teff': (5000, 50, 50, 'K')}},
                {'id': 'b', 'label': 'B', 'parameters': {'teff': (5100, 50, 50, 'K')}},
            ],
        )
        self.assertTrue(set_best_fit(path, 'b'))
        from analysis.auxil.fileio import read2dict
        data = read2dict(path)
        self.assertEqual(get_best_fit_id(data, category='spectral_fit'), 'b')
        os.unlink(path)

    def test_write_sed_obs_with_string_column(self):
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
            path = tmp.name
        dtype = np.dtype([('wave', 'f8'), ('photband', 'S8'), ('flux', 'f8'), ('flux_err', 'f8')])
        arr = np.array([(5000.0, b'G', 1e-12, 1e-13)], dtype=dtype)
        write_multi_fit_v2(
            path,
            category='sed_fit',
            hdf5_type='SF',
            measurements_data={'Obs': {'data': arr, 'attrs': {'datatype': 'discrete'}}},
            fits=[{'id': 'f1', 'label': 'SED', 'is_best_fit': True, 'parameters': {'teff1': (5000, 100, 100, 'K')}}],
        )
        with __import__('h5py').File(path, 'r') as hdf:
            self.assertIn('Obs', hdf['DATA'])
        os.unlink(path)

    def test_multi_fit_parameter_units_survive_read2dict(self):
        """Units stored as dataset attrs must be picked up after read2dict."""
        from analysis.auxil.fileio import read2dict
        from analysis.auxil import read_analyses

        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
            path = tmp.name
        write_multi_fit_v2(
            path,
            category='sed_fit',
            hdf5_type='SF',
            fits=[{
                'id': 'f1',
                'label': 'SED',
                'is_best_fit': True,
                'parameters': {
                    'teff': (44130.0, 100.0, 100.0, 'K'),
                    'ebv': (0.06, 0.01, 0.01, 'mag'),
                    'L': (2000.0, 50.0, 50.0, 'solLum'),
                },
            }],
        )
        data = read2dict(path)
        params = read_analyses.get_parameters(data)
        self.assertIn('teff', params)
        self.assertEqual(params['teff'][3], 'K')
        self.assertIn('ebv', params)
        self.assertIn('L', params)
        os.unlink(path)


class ContributorPermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user('owner', password='x')
        self.other = User.objects.create_user('other', password='x')
        self.rw = User.objects.create_user('rw', password='x')
        self.project = Project.objects.create(name='P', slug='p', is_public=False)
        self.project.readwriteown_users.add(self.owner)
        self.project.readwrite_users.add(self.rw)
        self.star = Star.objects.create(name='HD1', project=self.project, ra=1.0, dec=2.0)
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
            self.path = tmp.name
        write_rv_curve_v2(self.path, fits=[{
            'id': 'f1',
            'label': 'Fit 1',
            'is_best_fit': True,
            'parameters': {'K': (10.0, 1.0, 1.0, 'km/s')},
        }])
        from django.core.files import File
        with open(self.path, 'rb') as fh:
            self.analysis = Analysis.objects.create(
                project=self.project,
                star=self.star,
                category=AnalysisCategory.RV_CURVE,
                datafile=File(fh, name='rv.h5'),
            )
        sync_fits_from_hdf5(self.analysis)
        self.fit = self.analysis.fits.get(fit_id='f1')
        self.fit.uploaded_by = self.owner
        self.fit.save()

    def tearDown(self):
        try:
            os.unlink(self.path)
        except OSError:
            pass

    def test_readwriteown_cannot_delete_foreign_fit(self):
        self.assertFalse(user_can_delete_fit(self.other, self.fit))

    def test_owner_can_delete_own_fit(self):
        self.assertTrue(user_can_delete_fit(self.owner, self.fit))

    def test_readwrite_can_set_best_fit(self):
        self.assertTrue(user_can_set_best_fit(self.rw, self.analysis))
        self.assertFalse(user_can_set_best_fit(self.owner, self.analysis))


class ContributorApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('apiuser', password='x')
        self.project = Project.objects.create(name='API', slug='api', is_public=False)
        self.project.readwrite_users.add(self.user)
        self.star = Star.objects.create(name='HD9', project=self.project, ra=1.0, dec=2.0)
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
            self.path = tmp.name
        write_rv_curve_v2(self.path, fits=[{
            'id': 'base',
            'label': 'Base',
            'is_best_fit': True,
            'parameters': {'K': (10.0, 1.0, 1.0, 'km/s')},
        }])
        from django.core.files import File
        with open(self.path, 'rb') as fh:
            self.analysis = Analysis.objects.create(
                project=self.project,
                star=self.star,
                category=AnalysisCategory.RV_CURVE,
                datafile=File(fh, name='rv.h5'),
            )
        sync_fits_from_hdf5(self.analysis)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        try:
            os.unlink(self.path)
        except OSError:
            pass

    def test_best_fit_endpoint(self):
        two_fit_path = self.path + '.two.h5'
        write_rv_curve_v2(two_fit_path, fits=[
            {'id': 'base', 'label': 'Base', 'is_best_fit': True, 'parameters': {'K': (10.0, 1.0, 1.0, 'km/s')}},
            {'id': 'second', 'label': 'Second', 'parameters': {'K': (20.0, 1.0, 1.0, 'km/s')}},
        ])
        from django.core.files import File
        with open(two_fit_path, 'rb') as fh:
            analysis = Analysis.objects.create(
                project=self.project,
                star=Star.objects.create(name='HD10', project=self.project, ra=2.0, dec=3.0),
                category=AnalysisCategory.RV_CURVE,
                datafile=File(fh, name='rv2.h5'),
            )
        sync_fits_from_hdf5(analysis)
        resp = self.client.post(
            f'/api/analysis/analyses/{analysis.pk}/best-fit/',
            {'fit_id': 'second'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        analysis.refresh_from_db()
        best = analysis.fits.get(is_best_fit=True)
        self.assertEqual(best.fit_id, 'second')
        os.unlink(two_fit_path)

    def test_fit_parameters_endpoint(self):
        resp = self.client.get(f'/api/analysis/analyses/{self.analysis.pk}/fit-parameters/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['parameters'])


class SedMigrationTests(TestCase):
    def test_measurements_from_sed_obs_with_band_column(self):
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
            path = tmp.name
        import h5py
        dtype = np.dtype([('wave', 'f8'), ('photband', 'S8'), ('flux', 'f8'), ('flux_err', 'f8')])
        with h5py.File(path, 'w') as hdf:
            hdf.attrs['type'] = 'sedfit'
            data = hdf.create_group('DATA')
            data.create_dataset('Obs', data=np.array([(5000.0, b'G', 1e-12, 1e-13)], dtype=dtype))
            model = hdf.create_group('MODEL')
            mtype = np.dtype([('wave', 'f4'), ('flux', 'f4')])
            model.create_dataset('tmap', data=np.array([(5000.0, 1e-12)], dtype=mtype))
            params = hdf.create_group('PARAMETERS')
            ptype = np.dtype([('value', 'f8'), ('err_l', 'f8'), ('err_u', 'f8')])
            ds = params.create_dataset('teff1', data=np.array([(5000.0, 100.0, 100.0)], dtype=ptype))
            ds.attrs['unit'] = 'K'

        payload, attrs = _measurements_from_hdf5_path(path, AnalysisCategory.SED_FIT)
        self.assertIsNotNone(payload)
        self.assertIn('Obs', payload)

        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as out:
            out_path = out.name
        from analysis.auxil.multi_fit_hdf5 import write_multi_fit_v2
        write_multi_fit_v2(
            out_path,
            category='sed_fit',
            hdf5_type='SF',
            measurements_data=payload,
            data_group_attrs=attrs,
            fits=[{'id': 'x', 'label': 't', 'is_best_fit': True}],
        )
        os.unlink(path)
        os.unlink(out_path)
