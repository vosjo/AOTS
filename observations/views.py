from django.shortcuts import get_object_or_404, render, reverse
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib import messages

from django.db.models import Sum

from .models import (
    Spectrum,
    SpecFile,
    RawSpecFile,
    LightCurve,
    Observatory,
    )
from stars.models import Star, Project
from stars.auxil import invalid_form

from .forms import (
    UploadSpecFileForm,
    UploadRawSpecFileForm,
    UploadLightCurveForm,
    UploadSpectraDetailForm,
    SpectrumModForm,
    )

from .auxil import read_spectrum, read_lightcurve

from .plotting import plot_visibility, plot_spectrum, plot_lightcurve

from bokeh.resources import CDN
from bokeh.embed import components

from AOTS.custom_permissions import check_user_can_view_project


@check_user_can_view_project
def spectra_list(request, project=None,  **kwargs):
    """
        Spectra index page using datatables and restframework api
    """

    project = get_object_or_404(Project, slug=project)

    return render(request, 'observations/spectra_list.html', {'project': project})


@check_user_can_view_project
def spectrum_detail(request, spectrum_id, project=None,  **kwargs):
    '''
        Show detailed spectrum information
    '''

    #   Load project and spectrum
    project = get_object_or_404(Project, slug=project)
    spectrum = get_object_or_404(Spectrum, pk=spectrum_id)

    #   Check if spectrum should be rebinned
    #   -> those larger than 1 Mb get rebinned
    total_size = sum([s.specfile.size for s in spectrum.specfile_set.all()])
    if total_size > 500000:
        rebin = 10
        #request.GET._mutable = True
        #request.GET['rebin'] = 10
    else:
        rebin = 1

    #   Normalisation?
    normalize = None

    #   Specify default polynomial order for normalisation
    order = 3

    #   Check if user specified binning factor and normalization in the url
    if request.method == 'GET':
        rebin = int(request.GET.get('rebin', rebin))
        norm  = request.GET.get('normalize')
        if norm == 0:
            normalize = False
        elif norm == 1:
            normalize = True
        else:
            normalize = None

    #   Order all spectra
    all_instruments = spectrum.star.spectrum_set.values_list(
        'instrument',
        flat=True,
        )
    all_spectra = {}
    for inst in set(all_instruments):
        all_spectra[inst] = spectrum.star.spectrum_set.filter(instrument__exact=inst).order_by('hjd')

    #   Form to allow modification of the spectrum plot
    if request.method == 'POST':
        form = SpectrumModForm(request.POST)
        if form.is_valid():
            normalize = form.cleaned_data['normalize']
            order     = form.cleaned_data['order']
            rebin     = form.cleaned_data['binning']
    else:
        form = SpectrumModForm()

    #   Make plots
    vis  = plot_visibility(spectrum)
    spec = plot_spectrum(
        spectrum_id,
        rebin=rebin,
        normalize=normalize,
        porder=order,
        )

    #   Create HTML content
    script, div = components({'spec':spec, 'visibility':vis}, CDN)

    #   Make dict with the content
    context = {
        'project': project,
        'spectrum': spectrum,
        'all_spectra': all_spectra,
        'figures': div,
        'script': script,
        'form': form,
        'rebin': rebin,
    }

    return render(request, 'observations/spectrum_detail.html', context)


def add_spectra(request, project=None, **kwargs):
    '''
        Spectra upload page
    '''

    #   Set project
    project = get_object_or_404(Project, slug=project)

    #   Handle file upload
    if request.method == 'POST' and request.user.is_authenticated:
        if 'spectrumfile' in request.FILES:
            #   Get form
            upload_form = UploadSpectraDetailForm(request.POST, request.FILES)

            #   Check form validity
            if upload_form.is_valid():

                #   Get form data
                data = upload_form.cleaned_data

                #   Check submitted infos
                user_info = read_spectrum.check_form(data)

                #   Check if user information shall be added
                #       Set 'user_info' to an empty dict, if not
                if 'add_info' in user_info.keys():
                    add_info = user_info['add_info']
                    if not add_info:
                        user_info = {}
                else:
                    user_info = {}

                #   Provided parameters
                parameters = user_info.keys()

                #   Determine if a new system should be created
                #   Default: True
                if 'create_new_star' in parameters:
                    new = user_info['create_new_star']
                else:
                    new = True

                #   Check if observatory is set
                if 'observatory' in parameters:
                    obs    = user_info['observatory']
                    user_info['obs_pk'] = obs.pk

                #   Make new observatory?
                elif ('observatory_name' in parameters and
                     'observatory_latitude' in parameters and
                     'observatory_longitude' in parameters and
                     'observatory_altitude' in parameters):
                        obs_name      = user_info['observatory_name']
                        obs_latitude  = user_info['observatory_latitude']
                        obs_longitude = user_info['observatory_longitude']
                        obs_altitude  = user_info['observatory_altitude']
                        if 'observatory_is_spacecraft' in parameters:
                            obs_in_space=user_info['observatory_is_spacecraft']
                        else:
                            obs_in_space=True

                        observatory = Observatory(
                            project=project,
                            name=obs_name,
                            latitude=obs_latitude,
                            longitude=obs_longitude,
                            altitude=obs_altitude,
                            space_craft=obs_in_space,
                            )
                        observatory.save()
                        user_info['obs_pk'] = observatory.pk

                #   Get files
                files = request.FILES.getlist('spectrumfile')

                for f in files:
                    #   Save the new specfile
                    newspec = SpecFile(
                        specfile=f,
                        project=project,
                        added_by=request.user,
                        )
                    newspec.save()

                    #   Now process it and add it to a Spectrum and Object
                    try:
                        #   Process specfile
                        success, message = read_spectrum.process_specfile(
                            newspec.pk,
                            create_new_star=new,
                            user_info=user_info,
                            )
                        #   Set success/error message
                        if success:
                            level = messages.SUCCESS
                        else:
                            level = messages.ERROR
                        messages.add_message(request, level, message)

                        #   Refresh SpecFile from database
                        newspec.refresh_from_db()

                        if len(user_info) > 0:
                            #   Save user info in extra model
                            success, message = read_spectrum.add_userinfo(
                                user_info,
                                newspec.spectrum.pk,
                                added_by=request.user,
                                )

                            #   Set success/error message
                            if success:
                                level = messages.INFO
                            else:
                                level = messages.WARNING
                            messages.add_message(request, level, message)

                    except Exception as e:
                        #   Handel error
                        print(e)
                        newspec.delete()
                        messages.add_message(
                            request,
                            messages.ERROR,
                            "Exception occurred when adding: " + str(f),
                            )


                #   Return and redirect
                return HttpResponseRedirect(reverse(
                    'observations:specfile_list',
                    kwargs={'project':project.slug}
                    ))
            else:
                #   Handel invalid form
                invalid_form(
                    request,
                    'observations:spectra_upload',
                    project.slug,
                    )

    #   Block uploads by anonymous
    elif request.method != 'GET' and not request.user.is_authenticated:
        messages.add_message(
            request,
            messages.ERROR,
            "You need to login for that action!",
            )

    #   Initialize upload form
    upload_form = UploadSpectraDetailForm()

    #   Limit observatories to those of the project
    upload_form.fields['observatory'].queryset = Observatory.objects\
        .filter(project__exact=project)

    #   Set dict for the renderer
    context = {'project': project, 'upload_form': upload_form}

    return render(request, 'observations/spectra_upload.html', context)


@check_user_can_view_project
def specfile_list(request, project=None,  **kwargs):
    '''
        SpecFile index page
    '''

    #   Set project
    project = get_object_or_404(Project, slug=project)

    #   Set dict for the renderer
    context = {
        'project': project,
        #'upload_form': upload_form,
        #'raw_upload_form': raw_upload_form,
        }

    return render(request, 'observations/specfiles_list.html', context)


@check_user_can_view_project
def rawspecfile_list(request, project=None,  **kwargs):
    '''
        RawFile index page, including raw file upload
    '''

    #   Set project
    project = get_object_or_404(Project, slug=project)

    #   Initialize upload forms
    raw_upload_form = UploadRawSpecFileForm()
    raw_upload_form.fields['system'].queryset = Star.objects\
        .filter(project__exact=project.pk)\
        .exclude(spectrum__isnull=True)
    raw_upload_form.fields['specfile'].queryset = SpecFile.objects\
        .filter(project__exact=project.pk)

    # Handle file upload
    if request.method == 'POST' and request.user.is_authenticated:
        #   Raw files
        if 'rawfile' in request.FILES:

            #   Get form
            raw_upload_form = UploadRawSpecFileForm(request.POST, request.FILES)
            if raw_upload_form.is_valid():
                #   Read selected Specfile
                specfiles = raw_upload_form.cleaned_data['specfile']

                message_list = []

                #   Get files
                files = request.FILES.getlist('rawfile')
                for f in files:
                    #    Save the new raw file
                    newrawspec = RawSpecFile(
                        project=project,
                        added_by=request.user,
                        )
                    newrawspec.save()
                    newrawspec.rawfile.save(f.name, f)

                    #    Now process it and check for duplicates
                    try:
                        #   Process raw file
                        success, message = read_spectrum.process_raw_spec(
                            newrawspec.pk,
                            specfiles,
                            )

                        #   Set success/error message
                        if success:
                            level = messages.SUCCESS
                        else:
                            level = messages.ERROR
                        message_list.append([success, message])
                    except Exception as e:
                        #   Handel error
                        print(e)
                        newrawspec.delete()
                        message_text = "Exception occurred when adding: "+str(f)
                        message_list.append([False, message_text])

                return JsonResponse(
                    {'info':'Data uploaded', 'messages':message_list}
                    )

    #   Block uploads by anonymous
    elif request.method != 'GET' and not request.user.is_authenticated:
        messages.add_message(
            request,
            messages.ERROR,
            "You need to login for that action!",
            )

    #   Set dict for the render
    context = {
        'project': project,
        'raw_upload_form': raw_upload_form,
        }

    return render(request, 'observations/rawspecfiles_list.html', context)


@check_user_can_view_project
def lightcurve_list(request, project=None,  **kwargs):
   """
       Lightcurve index page using datatables and restframework api
   """

   project = get_object_or_404(Project, slug=project)

   upload_form = UploadLightCurveForm()


   # Handle file upload
   if request.method == 'POST' and request.user.is_authenticated:
      if 'lcfile' in request.FILES:
         upload_form = UploadLightCurveForm(request.POST, request.FILES)
         if upload_form.is_valid():

            files = request.FILES.getlist('lcfile')
            for f in files:
               #-- save the new specfile
               newlc = LightCurve(lcfile=f, project=project, added_by=request.user)
               newlc.save()

               #-- now process it and add it to a Spectrum and Object
               try:
                  success, message = read_lightcurve.process_lightcurve(newlc.pk, create_new_star=True)
                  level = messages.SUCCESS if success else messages.ERROR
                  messages.add_message(request, level, message)
               except Exception as e:
                  print(e)
                  newlc.delete()
                  messages.add_message(request, messages.ERROR, "Exception occured when adding: " + str(f))


            return HttpResponseRedirect(reverse('observations:lightcurve_list', kwargs={'project':project.slug}))

   elif request.method != 'GET' and not request.user.is_authenticated:
      messages.add_message(request, messages.ERROR, "You need to login for that action!")


   context = {'project': project, 'upload_form': upload_form}

   return render(request, 'observations/lightcurve_list.html', context)


@check_user_can_view_project
def lightcurve_detail(request, lightcurve_id, project=None,  **kwargs):
    '''
        Show detailed information to lightcurves
    '''

    project = get_object_or_404(Project, slug=project)

    lightcurve = get_object_or_404(LightCurve, pk=lightcurve_id)

    context = {'period' : None}

    period, binsize = None, 0.001
    if request.method == 'GET':
        period = request.GET.get('period', None)
        try:
            period = float(period) / 24.
            context['period'] = period * 24.0
        except Exception:
            period = None

        binsize = request.GET.get('binsize', 0.001)
        try:
            binsize = float(binsize)
        except Exception:
            binsize = 0.001

        context['binsize'] = binsize

    #-- order all lightcurves belonging to the same star
    all_instruments = lightcurve.star.lightcurve_set.values_list(
        'instrument',
        flat=True,
        )
    all_lightcurves = {}
    for inst in set(all_instruments):
        all_lightcurves[inst] = lightcurve.star.lightcurve_set\
            .filter(instrument__exact=inst).order_by('hjd')

    vis = plot_visibility(lightcurve)
    lc_time, lc_phase = plot_lightcurve(
        lightcurve_id,
        period=period,
        binsize=binsize,
        )
    script, div = components(
        {'lc_time':lc_time, 'lc_phase':lc_phase, 'visibility':vis},
        CDN
        )

    context['project'] =  project
    context['lightcurve'] = lightcurve
    context['all_lightcurves'] = all_lightcurves
    context['figures'] = div
    context['script'] = script

    return render(request, 'observations/lightcurve_detail.html', context)


@check_user_can_view_project
def observatory_list(request, project=None,  **kwargs):
    """
        Observatory index page using datatables and restframework api
    """

    project = get_object_or_404(Project, slug=project)

    return render(request, 'observations/observatory_list.html', {'project': project})
