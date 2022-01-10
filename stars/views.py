import sys
import csv

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Star, Tag, Project
from analysis.models import Method, DataSet, DataSource, Parameter
from analysis import models as analModels

from observations.plotting import plot_sed

import io
from .forms import StarForm, UploadSystemForm, UploadSystemDetailForm

# from .plotting import plot_photometry

from bokeh.resources import CDN
from bokeh.embed import components

from AOTS.custom_permissions import check_user_can_view_project

import logging
import json


# Create your views here.

def project_list(request):
    """
   Simplified view of the project page
   """

    public_projects = Project.objects.filter(is_public__exact=True).order_by('name')
    private_projects = None

    if not request.user.is_anonymous:
        user = request.user
        private_projects = Project.objects.filter(is_public__exact=False) \
            .filter(pk__in=user.get_read_projects().values('pk')).order_by('name')

    context = {'public_projects': public_projects,
               'private_projects': private_projects,
               }

    return render(request, 'stars/project_list.html', context)


@check_user_can_view_project
def star_list(request, project=None, **kwargs):
    project = get_object_or_404(Project, slug=project)

    upload_form = UploadSystemForm()
    upload_form_detail = UploadSystemDetailForm()

    #   Handle uploads
    if request.method == 'POST' and request.user.is_authenticated:
        #   Handle file upload
        #   File upload, if 'system' in request
        if 'system' in request.FILES:

            upload_form = UploadSystemForm(request.POST, request.FILES)
            if upload_form.is_valid():
                files = request.FILES.getlist('system')
                for f in files:
                    filename = f.name
                    if ".csv" not in filename:
                        messages.add_message(
                            request,
                            messages.ERROR,
                            "Exception: {} is not a .csv file".format(f.name),
                        )
                        continue
                    systems = csv.DictReader(io.TextIOWrapper(f.file))
                    for star in systems:
                        try:
                            success, message = mk_new_system(star, project)
                            l = messages.SUCCESS if success else messages.ERROR
                            messages.add_message(request, l, message)
                        except Exception as e:
                            print(e)
                            messages.add_message(
                                request,
                                messages.ERROR,
                                "Exception occurred when adding: " + str(f.name),
                            )
                        # except:
                        # messages.add_message(
                        # request,
                        # messages.ERROR,
                        # "Exception occured when adding: "\
                        # +str(star["main_id"]),
                        # )

                return HttpResponseRedirect(reverse(
                    'systems:star_list',
                    kwargs={'project': project.slug},
                ))
        else:
            upload_form_detail = UploadSystemDetailForm(
                request.POST,
                request.FILES,
            )
            if upload_form_detail.is_valid():
                try:
                    success, message = mk_new_system(
                        upload_form_detail.cleaned_data,
                        project,
                    )
                    level = messages.SUCCESS if success else messages.ERROR
                    messages.add_message(request, level, message)
                except Exception as e:
                    print(e)
                    messages.add_message(
                        request,
                        messages.ERROR,
                        "Exception occurred when adding a system",
                    )

                return HttpResponseRedirect(reverse(
                    'systems:star_list',
                    kwargs={'project': project.slug},
                ))
            else:

                print("invalid")
                print(upload_form_detail.cleaned_data)

    elif request.method != 'GET' and not request.user.is_authenticated:
        messages.add_message(
            request,
            messages.ERROR,
            "You need to login for that action!",
        )

    context = {
        'project': project,
        'upload_form': upload_form,
        'form_detail': upload_form_detail,
    }

    return render(request, 'stars/star_list.html', context)


def mk_new_system(star, project):
    ##### TODO: ADD HERE A REAL FUNCTION: #####
    #   Function to identify RA AND DEC input and convert it to deg
    ra = float(star['ra'])
    dec = float(star['dec'])
    ###########################################

    #   Check for duplicates
    duplicates = Star.objects.filter(name=star["main_id"]) \
        .filter(ra__range=[ra - 1 / 3600., ra + 1 / 3600.]) \
        .filter(dec__range=[dec - 1 / 3600., dec + 1 / 3600.]) \
        .filter(project__exact=project.pk)

    # print("duplicates", duplicates)

    if len(duplicates) != 0:
        return False, "System exists already: " + star["main_id"]

    #   Initialize star model
    sobj = Star(
        name=star["main_id"],
        project=project,
        ra=ra,
        dec=dec,
        classification=star['sp_type'],
        classification_type='PH',
        observing_status='ON',
    )
    sobj.save()

    ident = sobj.identifier_set.all()[0]
    ident.href = "http://simbad.u-strasbg.fr/simbad/" \
                 + "sim-id?Ident=" + star['main_id'] \
                     .replace(" ", "").replace('+', "%2B")
    ident.save()

    if 'JNAME' in star:
        sobj.identifier_set.create(name=star['JNAME'])

    # -- Add Tags
    if 'tags' in star:
        for tag in star["tags"]:
            sobj.tags.add(tag)

    #-- Add photometry
    #   Internal photometry names
    passbands = [
        'GAIA2.G',
        'GAIA2.BP',
        'GAIA2.RP',
        '2MASS.J',
        '2MASS.H',
        '2MASS.K',
        'WISE.W1',
        'WISE.W2',
        'WISE.W3',
        'WISE.W4',
        'GALEX.FUV',
        'GALEX.NUV',
        'SKYMAP.U',
        'SKYMAP.V',
        'SKYMAP.G',
        'SKYMAP.R',
        'SKYMAP.I',
        'SKYMAP.Z',
        'APASS.B',
        'APASS.V',
        'APASS.G',
        'APASS.R',
        'APASS.I',
        'SDSS.U',
        'SDSS.G',
        'SDSS.R',
        'SDSS.I',
        'SDSS.Z',
        'PANSTAR.G',
        'PANSTAR.R',
        'PANSTAR.I',
        'PANSTAR.Z',
        'PANSTAR.Y',
    ]
    #   CSV or form names
    photnames = [
        'phot_g_mean_mag',
        'phot_bp_mean_mag',
        'phot_rp_mean_mag',
        'Jmag',
        'Hmag',
        'Kmag',
        'W1mag',
        'W2mag',
        'W3mag',
        'W4mag',
        'FUV',
        'NUV',
        'Umag',
        'Vmag',
        'Gmag',
        'Rmag',
        'Imag',
        'Zmag',
        'APBmag',
        'APVmag',
        'APGmag',
        'APRmag',
        'APImag',
        'SDSSUmag',
        'SDSSGmag',
        'SDSSRmag',
        'SDSSImag',
        'SDSSZmag',
        'PANGmag',
        'PANRmag',
        'PANImag',
        'PANZmag',
        'PANYmag'
    ]
    #   Error names
    errs = ['phot_g_mean_magerr',
            'phot_bp_mean_magerr',
            'phot_rp_mean_magerr',
            'Jmagerr',
            'Hmagerr',
            'Kmagerr',
            'W1magerr',
            'W2magerr',
            'W3magerr',
            'W4magerr',
            'FUVerr',
            'NUVerr',
            'Umagerr',
            'Vmagerr',
            'Gmagerr',
            'Rmagerr',
            'Imagerr',
            'Zmagerr',
            'APBmagerr',
            'APVmagerr',
            'APGmagerr',
            'APRmagerr',
            'APImagerr',
            'SDSSUmagerr',
            'SDSSGmagerr',
            'SDSSRmagerr',
            'SDSSImagerr',
            'SDSSZmagerr',
            'PANGmagerr',
            'PANRmagerr',
            'PANImagerr',
            'PANZmagerr',
            'PANYmagerr']

    for i, phot in enumerate(photnames):
        #   Check if photometry band was provided
        if phot in star:
            #   Check if photometry error was provided
            if phot in star:
                if errs[i] in star:
                    if (star[phot] != None and star[phot] != "" and
                        star[errs[i]] != None and star[errs[i]] != ""):
                        sobj.photometry_set.create(
                            band=passbands[i],
                            measurement=star[phot],
                            error=star[errs[i]],
                            unit='mag',
                        )
                    elif star[phot] != None and star[phot] != "":
                        sobj.photometry_set.create(
                            band=passbands[i],
                            measurement=star[phot],
                            error=0.,
                            unit='mag',
                        )
                else:
                    if star[phot] != None and star[phot] != "":
                        sobj.photometry_set.create(
                            band=passbands[i],
                            measurement=star[phot],
                            error=0.,
                            unit='mag',
                        )

    # -- Add parameters from gaia DR2
    if (star['parallax'] != None or
        star['pmra_x'] != None or
        star['pmdec_x'] != None):

        try:
            dsgaia = DataSource.objects.get(
                name__exact='Gaia DR2',
                project=project,
            )
        except DataSource.DoesNotExist:
            dsgaia = DataSource.objects.create(
                name='Gaia DR2',
                note='2nd Gaia data release',
                reference='https://doi.org/10.1051/0004-6361/201833051',
                project=project,
            )

        if star['parallax'] != None:
            sobj.parameter_set.create(
                data_source=dsgaia,
                name='parallax',
                component=0,
                value=star['parallax'],
                error=star['parallax_error'],
                unit='',
            )

        if star['pmra_x'] != None:
            sobj.parameter_set.create(
                data_source=dsgaia,
                name='pmra',
                component=0,
                value=star['pmra_x'],
                error=star['pmra_error'],
                unit='mas',
            )

        if star['pmdec_x'] != None:
            sobj.parameter_set.create(
                data_source=dsgaia,
                name='pmdec',
                component=0,
                value=star['pmdec_x'],
                error=star['pmdec_error'],
                unit='mas',
            )

    sobj.save()

    return True, ""


@check_user_can_view_project
def tag_list(request, project=None, **kwargs):
    """
   Simple view showing all defined tags, and allowing for deletion and creation of new ones.
   Tag retrieval, deletion and creation is handled through the API
   """

    project = get_object_or_404(Project, slug=project)

    return render(request, 'stars/tag_list.html', {'project': project})


@check_user_can_view_project
def star_detail(request, star_id, project=None, **kwargs):
    """
   Detailed view for star
   interesting for input fields: https://leaverou.github.io/awesomplete/
   and also: https://gist.github.com/conor10/8085ac62fd81ad3002e582d1be65c398
   """
    project = get_object_or_404(Project, slug=project)

    star = get_object_or_404(Star, pk=star_id)
    context = {
        'star': star,
        'tags': Tag.objects.all(),
        'project': project,
    }

    # -- make related systems list, but only show 10 systems befor and after the current system to avoid long loading times
    tags = star.tags.all()
    related_stars = []
    for tag in tags:
        s1 = tag.stars.filter(ra__lt=star.ra).order_by('-ra')
        s2 = tag.stars.filter(ra__gt=star.ra).order_by('ra')

        related_stars.append({'tag': tag,
                              'stars_lower': s1[:10][::-1],
                              'stars_upper': s2[:10],
                              'stars_lower_hidden': max(0, len(s1) - 10),
                              'stars_upper_hidden': max(0, len(s2) - 10), })

    context['related_stars'] = related_stars

    # -- add analysis methods
    methods = Method.objects.all()

    datasets, figures = [], []

    figures.append(plot_sed(star.pk))

    for method in methods:
        dataset = star.dataset_set.filter(method__exact=method)
        if dataset:
            dataset = dataset[0]
            figures.append(dataset.make_figure())
            datasets.append(dataset)

    if len(figures) > 0:
        # -- Make the bokeh figures and add them to the dataset
        script, div = components(figures, CDN)

        datasections = []
        for fig, dataset in zip(div[1:], datasets):
            datasections.append((fig, dataset))

        context['datasets'] = datasections
        context['sed_plot'] = div[0]
        context['script'] = script

    # -- get all parameters for the parameter overview
    component_names = {0: 'System', 1: 'Primary', 2: 'Secondary'}

    parameters = []
    pSource_pks = star.parameter_set.values_list('data_source').distinct()
    pSource = DataSource.objects.filter(id__in=pSource_pks).order_by('name')

    for comp in [analModels.SYSTEM, analModels.PRIMARY, analModels.SECONDARY]:
        pNames = star.parameter_set.filter(component__exact=comp,
                                           valid__exact=True).values_list('name').distinct()
        pNames = sorted([name[0] for name in pNames], key=analModels.parameter_order)

        allParameters = star.parameter_set.all().filter(component__exact=comp)

        params = []
        for name in pNames:
            values, pinfo = [], None
            for source in pSource:
                try:
                    p = allParameters.get(name__exact=name, data_source__exact=source.pk)
                    values.append(r"{} &pm; {}".format(p.rvalue(), p.rerror()))
                    pinfo = p
                except Exception as e:
                    values.append("/")

            params.append({'values': values, 'pinfo': pinfo})

        parameters.append({'params': params, 'component': component_names[comp]})

    context['allParameters'] = parameters
    context['parameterSources'] = pSource

    return render(request, 'stars/star_detail.html', context)


@check_user_can_view_project
@login_required
def star_edit(request, star_id, project=None, **kwargs):
    """
   View to handle editing of the basic star details
   """

    project = get_object_or_404(Project, slug=project)

    star = get_object_or_404(Star, pk=star_id)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':

        if request.POST.get("delete"):
            # Delete this star and return to index
            messages.success(request, "The system: {} was successfully deleted".format(star.name))
            star.delete()
            return redirect('systems:star_list', project.slug)

        else:
            # Update the star based on the form
            form = StarForm(request.POST, instance=star)

            # check if the input was valid
            if form.is_valid():
                star = form.save()

                # redirect details page
                messages.success(request, "This system was successfully updated")
                return redirect('systems:star_detail', project.slug, star.pk)


    # if a GET (or any other method) create a form for the given star
    else:
        form = StarForm(instance=star)

    return render(request, 'stars/star_edit.html', {'form': form, 'star': star, 'project': project})
