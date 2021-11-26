from django.shortcuts import get_object_or_404, render, reverse
from django.http import HttpResponseRedirect
from django.contrib import messages

from django.db.models import Sum

from .models import Spectrum, SpecFile, LightCurve, Observatory, RawSpecFile
from stars.models import Star, Project

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
   simplified version of spectra index page using datatables and restframework api
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
    }

    return render(request, 'observations/spectrum_detail.html', context)


def add_spectra(request, project=None, **kwargs):

   project = get_object_or_404(Project, slug=project)

   print ("add spectrum" )


   # Handle file upload
   if request.method == 'POST' and request.user.is_authenticated:
      if 'spectrumfile' in request.FILES:
         upload_form = UploadSpectraDetailForm(request.POST, request.FILES)

         if upload_form.is_valid():

            print( "valid")
            print (upload_form.cleaned_data)

         else:

            print( "invalid")
            print (upload_form.cleaned_data)

            #files = request.FILES.getlist('specfile')
            #for f in files:
               ##-- save the new specfile
               #newspec = SpecFile(specfile=f, project=project, added_by=request.user)
               #newspec.save()

               ##-- now process it and add it to a Spectrum and Object
               #try:
                  #success, message = read_spectrum.process_specfile(newspec.pk, create_new_star=True)
                  #level = messages.SUCCESS if success else messages.ERROR
                  #messages.add_message(request, level, message)
               #except Exception as e:
                  #print(e)
                  #newspec.delete()
                  #messages.add_message(request, messages.ERROR, "Exception occured when adding: " + str(f))


            #return HttpResponseRedirect(reverse('observations:specfile_list', kwargs={'project':project.slug}))

   #elif request.method != 'GET' and not request.user.is_authenticated:
      #messages.add_message(request, messages.ERROR, "You need to login for that action!")

   upload_form = UploadSpectraDetailForm()

   upload_form.fields['observatory'].queryset = Observatory.objects.filter(project__exact=project)


   context = {'project': project, 'upload_form': upload_form}

   return render(request, 'observations/spectra_new.html', context)


@check_user_can_view_project
def specfile_list(request, project=None,  **kwargs):

    #   Set project
    project = get_object_or_404(Project, slug=project)

    #   Initialize upload forms
    upload_form = UploadSpecFileForm()
    raw_upload_form = UploadRawSpecFileForm()

    # Handle file upload
    if request.method == 'POST' and request.user.is_authenticated:
        #   Specfiles:
        if 'specfile' in request.FILES:
            #   Get form
            upload_form = UploadSpecFileForm(request.POST, request.FILES)
            if upload_form.is_valid():
                #   Get files
                files = request.FILES.getlist('specfile')
                for f in files:
                    #   Save the new specfile
                    newspec = SpecFile(
                        specfile=f,
                        project=project,
                        added_by=request.user,
                        #filename=f.name,
                        )
                    newspec.save()

                    #   Now process it and add it to a Spectrum and Object
                    try:
                        #   Process specfile
                        success, message = read_spectrum.process_specfile(
                            newspec.pk,
                            create_new_star=True,
                            )
                        #   Set success/error message
                        if success:
                            level = messages.SUCCESS
                        else:
                            level = messages.ERROR
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

        #   Raw files
        if 'rawfile' in request.FILES:
            #   Get form
            raw_upload_form = UploadRawSpecFileForm(request.POST, request.FILES)
            if raw_upload_form.is_valid():
                #   Name of the Specfile
                specfile_name = raw_upload_form.cleaned_data['specfile_name']

                #   Get files
                files = request.FILES.getlist('rawfile')
                for f in files:
                    #    Save the new raw file
                    newrawspec = RawSpecFile(
                        rawfile=f,
                        project=project,
                        added_by=request.user,
                        #filename=f.name,
                        #specfile=,
                        )
                    newrawspec.save()

                    #    Now process it and add it to a Specfile
                    try:
                        #   Process raw file
                        success, message = read_spectrum.process_raw_spec(
                            newrawspec.pk,
                            specfile_name,
                            )
                        #   Set success/error message
                        if success:
                            level = messages.SUCCESS
                        else:
                            level = messages.ERROR
                        messages.add_message(request, level, message)
                    except Exception as e:
                        #   Handel error
                        print(e)
                        #newrawspec.rawfile.delete()
                        newrawspec.delete()
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
        'upload_form': upload_form,
        'raw_upload_form': raw_upload_form,
        }

    return render(request, 'observations/specfiles_list.html', context)


@check_user_can_view_project
def rawspecfile_list(request, project=None,  **kwargs):

    #   Set project
    project = get_object_or_404(Project, slug=project)

    #   Initialize upload forms
    raw_upload_form = UploadRawSpecFileForm()

    # Handle file upload
    if request.method == 'POST' and request.user.is_authenticated:
        #   Raw files
        if 'rawfile' in request.FILES:
            #   Get form
            raw_upload_form = UploadRawSpecFileForm(request.POST, request.FILES)
            if raw_upload_form.is_valid():
                #   Name of the Specfile
                specfile_name = raw_upload_form.cleaned_data['specfile_name']

                #   Get files
                files = request.FILES.getlist('rawfile')
                for f in files:
                    #    Save the new raw file
                    newrawspec = RawSpecFile(
                        rawfile=f,
                        project=project,
                        added_by=request.user,
                        #filename=f.name,
                        #specfile=,
                        )
                    newrawspec.save()

                    #    Now process it and add it to a raw file
                    try:
                        #   Process raw file
                        success, message = read_spectrum.process_raw_spec(
                            newrawspec.pk,
                            specfile_name,
                            )
                        #   Set success/error message
                        if success:
                            level = messages.SUCCESS
                        else:
                            level = messages.ERROR
                        messages.add_message(request, level, message)
                    except Exception as e:
                        #   Handel error
                        print(e)
                        #newrawspec.rawfile.delete()
                        newrawspec.delete()
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
   simplified version of spectra index page using datatables and restframework api
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
   #-- show detailed spectrum information

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
   all_instruments = lightcurve.star.lightcurve_set.values_list('instrument', flat=True)
   all_lightcurves = {}
   for inst in set(all_instruments):
      all_lightcurves[inst] = lightcurve.star.lightcurve_set.filter(instrument__exact=inst).order_by('hjd')

   vis = plot_visibility(lightcurve)
   lc_time, lc_phase = plot_lightcurve(lightcurve_id, period=period, binsize=binsize)
   script, div = components({'lc_time':lc_time, 'lc_phase':lc_phase, 'visibility':vis}, CDN)


   context['project'] =  project
   context['lightcurve'] = lightcurve
   context['all_lightcurves'] = all_lightcurves
   context['figures'] = div
   context['script'] = script

   return render(request, 'observations/lightcurve_detail.html', context)


@check_user_can_view_project
def observatory_list(request, project=None,  **kwargs):
   """
   simplified version of observatory index page using datatables and restframework api
   """

   project = get_object_or_404(Project, slug=project)

   return render(request, 'observations/observatory_list.html', {'project': project})
