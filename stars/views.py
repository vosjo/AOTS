import csv
import io

from bokeh.embed import components
from bokeh.resources import CDN
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect, reverse

from AOTS.custom_permissions import check_user_can_view_project
from analysis.models import Method
from observations.plotting import plot_sed
from .auxil import populate_system, invalid_form, update_photometry, get_params, update_parameters
from .forms import (
    StarForm,
    UploadSystemForm,
    UploadSystemDetailForm,
    UpdatePhotometryForm, UpdateParamsForm,
)
from .models import Star, Tag, Project


# from .plotting import plot_photometry


# Create your views here.

def project_list(request):
    """
        Simplified view of the project page
    """

    public_projects = Project.objects \
        .filter(is_public__exact=True).order_by('name')
    private_projects = None

    if not request.user.is_anonymous:
        user = request.user
        private_projects = Project.objects \
            .filter(is_public__exact=False) \
            .filter(pk__in=user.get_read_projects().values('pk')) \
            .order_by('name')

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
                        #   Initialize star model
                        sobj = Star(
                            name=star["main_id"],
                            project=project,
                            ra=0.,
                            dec=0.,
                        )
                        sobj.save()

                        try:
                            success, message = populate_system(star, sobj.pk)
                            l = messages.SUCCESS if success else messages.ERROR
                            messages.add_message(request, l, message)
                        except Exception as e:
                            #   Handel error
                            print(e)
                            sobj.delete()
                            messages.add_message(
                                request,
                                messages.ERROR,
                                "Exception occurred when adding: {}".format(
                                    str(f.name)
                                ),
                            )

                return HttpResponseRedirect(reverse(
                    'systems:star_list',
                    kwargs={'project': project.slug},
                ))

            else:
                #   Handel invalid form
                invalid_form(request, 'systems:star_list', project.slug)

        else:
            upload_form_detail = UploadSystemDetailForm(
                request.POST,
                request.FILES,
            )
            if upload_form_detail.is_valid():
                #   Uploaded data
                star = upload_form_detail.cleaned_data

                #   Initialize star model
                sobj = Star(
                    name=star["main_id"],
                    project=project,
                    ra=0.,
                    dec=0.,
                )
                sobj.save()

                try:
                    success, message = populate_system(star, sobj.pk)
                    level = messages.SUCCESS if success else messages.ERROR
                    messages.add_message(request, level, message)
                except Exception as e:
                    print(e)
                    sobj.delete()
                    messages.add_message(
                        request,
                        messages.ERROR,
                        "Exception occurred when adding: {}".format(
                            star["main_id"]
                        ),
                    )

                return HttpResponseRedirect(reverse(
                    'systems:star_list',
                    kwargs={'project': project.slug},
                ))
            else:
                #   Handel invalid form
                invalid_form(request, 'systems:star_list', project.slug)

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


@check_user_can_view_project
def tag_list(request, project=None, **kwargs):
    """
        Simple view showing all defined tags, and allowing for deletion and
        creation of new ones. Tag retrieval, deletion and creation is handled
        through the API
    """

    project = get_object_or_404(Project, slug=project)

    return render(request, 'stars/tag_list.html', {'project': project})


@check_user_can_view_project
def star_detail(request, star_id, project=None, **kwargs):
    """
        Detailed view for star
        - interesting for input fields: https://leaverou.github.io/awesomplete/
          and also:
          https://gist.github.com/conor10/8085ac62fd81ad3002e582d1be65c398
    """
    project = get_object_or_404(Project, slug=project)
    update_phot_form = UpdatePhotometryForm()

    update_params_form = UpdateParamsForm(star_id=star_id)

    star = get_object_or_404(Star, pk=star_id)
    context = {
        'star': star,
        'tags': Tag.objects.filter(project__exact=project),
        'project': project,
        'update_phot_form': update_phot_form,
        'update_params_form': update_params_form,
    }

    #   Make related systems list, but only show 10 systems before and after the
    #   current system to avoid long loading times
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

    #   Add analysis methods
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
        #   Make the bokeh figures and add them to the dataset
        script, div = components(figures, CDN)

        datasections = []
        for fig, dataset in zip(div[1:], datasets):
            datasections.append((fig, dataset))

        context['datasets'] = datasections
        context['sed_plot'] = div[0]
        context['script'] = script

    parameters, pSource = get_params(star_id)

    if request.method == 'POST' and request.user.is_authenticated:
        # Differentiate between Vizier and Edit form submit buttons
        if "vizierbtn" not in request.POST:
            if "parambtn" in request.POST:
                update_params_form = UpdateParamsForm(
                    star_id=star_id,
                    data=request.POST
                )
                if update_params_form.is_valid():
                    try:
                        success, message = update_parameters(
                            update_params_form.cleaned_data,
                            project,
                            star_id
                        )
                        level = messages.SUCCESS if success else messages.ERROR
                        messages.add_message(request, level, message)
                    except Exception as e:
                        print(e)
                        messages.add_message(
                            request,
                            messages.ERROR,
                            "Exception occurred while updating photometry",
                        )

                    return HttpResponseRedirect(reverse(
                        'systems:star_detail',
                        kwargs={'project': project.slug,
                                "star_id": star_id},
                    ))
                else:
                    #   Handle invalid form
                    print(update_params_form.errors)
                    invalid_form(request, 'systems:star_detail', project.slug, star_id=star_id)
            update_phot_form = UpdatePhotometryForm(
                request.POST,
                request.FILES,
            )
            if update_phot_form.is_valid():
                try:
                    success, message = update_photometry(
                        update_phot_form.cleaned_data,
                        project,
                        star_id,
                        False
                    )
                    level = messages.SUCCESS if success else messages.ERROR
                    messages.add_message(request, level, message)
                except Exception as e:
                    print(e)
                    messages.add_message(
                        request,
                        messages.ERROR,
                        "Exception occurred while updating photometry",
                    )

                return HttpResponseRedirect(reverse(
                    'systems:star_detail',
                    kwargs={'project': project.slug,
                            "star_id": star_id},
                ))
            else:
                #   Handle invalid form
                invalid_form(request, 'systems:star_detail', project.slug, star_id=star_id)
        else:
            try:
                success, message = update_photometry(
                    None,
                    project,
                    star_id,
                    True
                )
                level = messages.SUCCESS if success else messages.ERROR
                messages.add_message(request, level, message)
            except Exception as e:
                print(e)
                messages.add_message(
                    request,
                    messages.ERROR,
                    "Exception occurred while updating photometry",
                )

            return HttpResponseRedirect(reverse(
                'systems:star_detail',
                kwargs={'project': project.slug,
                        "star_id": star_id},
            ))
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

    #   If this is a POST request we need to process the form data
    if request.method == 'POST':

        if request.POST.get("delete"):
            #   Delete this star and return to index
            messages.success(request, "The system: {} was successfully deleted".format(star.name))
            star.delete()
            return redirect('systems:star_list', project.slug)

        else:
            #   Update the star based on the form
            form = StarForm(request.POST, instance=star)

            #   Check if the input was valid
            if form.is_valid():
                star = form.save()

                #   Redirect details page
                messages.success(request, "This system was successfully updated")
                return redirect('systems:star_detail', project.slug, star.pk)


    #   If a GET (or any other method) create a form for the given star
    else:
        form = StarForm(instance=star)

    return render(request, 'stars/star_edit.html', {'form': form, 'star': star, 'project': project})
