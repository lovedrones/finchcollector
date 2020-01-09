from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

import uuid 
import boto3
from .models import Finch, Toy, Photo
from .forms import FeedingForm

S3_BASE_URL = 'https://s3-us-west-1.amazonaws.com/'
BUCKET = 'finchcollector-jlo'

def home(request):
    return render(request,'home.html')

def about(request):
    return render(request, 'about.html')

@login_required
def finches_index(request):
    finches = Finch.objects.filter(user=request.user)
    return render(request, 'finches/index.html', {
    'finches': finches
  })    

@login_required
def finches_detail(request, finch_id):
  finch = Finch.objects.get(id=finch_id)  
  toys_finch_doesnt_have = Toy.objects.exclude(id__in = finch.toys.all().values_list('id'))
  feeding_form = FeedingForm()
  return render(request, 'finches/detail.html', {
      'finch': finch, 'feeding_form': feeding_form,
      'toys': toys_finch_doesnt_have
  })


class FinchCreate(LoginRequiredMixin, CreateView):
    model = Finch
    fields = ['name', 'breed', 'description', 'age']
    

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class FinchUpdate(UpdateView):
    model = Finch
    fields = ['breed', 'description', 'age']

class FinchDelete(DeleteView):
    model = Finch
    success_url = '/finches/'

@login_required
def add_feeding(request, finch_id):
    form = FeedingForm(request.POST)
    if form.is_valid():
      new_feeding = form.save(commit=False)
      new_feeding.finch_id = finch_id
      new_feeding.save()
    return redirect('detail', finch_id=finch_id)



class ToyList(ListView):
    model = Toy 

class ToyDetail(DetailView):
    model = Toy

class ToyCreate(CreateView):
    model = Toy
    fields = '__all__'

class ToyUpdate(UpdateView):
    model = Toy
    fields = ['name', 'color']

class ToyDelete(DeleteView):
    model = Toy 
    success_url = '/toys/'    

@login_required
def assoc_toy(request, finch_id, toy_id):
  finch = Finch.objects.get(id=finch_id)
  finch.toys.add(toy_id)
  return redirect(finch)

@login_required
def add_photo(request, finch_id):
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
        s3 = boto3.client('s3')
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        try:
            s3.upload_fileobj(photo_file, BUCKET, key)
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            photo = Photo(url=url, finch_id=finch_id)
            photo.save()
        except:
            print('An error occurred uploading file to S3')
    return redirect('detail', finch_id=finch_id)  

def signup(request):
    error_message = ''
    if request.method == 'POST':
    # This is how to create a 'user' form object
    # that includes the data from the browser
      form = UserCreationForm(request.POST)
      if form.is_valid():
      # This will add the user to the database
        user = form.save()
      # This is how we log a user in via code
        login(request, user)
        return redirect('index')
      else:
        error_message = 'Invalid sign up - try again'
  # A bad POST or a GET request, so render signup.html with an empty form
    form = UserCreationForm()
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)