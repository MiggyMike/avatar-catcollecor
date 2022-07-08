from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import uuid
import boto3
from .models import Cat, Toy, Photo
from .forms import FeedingForm

S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'catcollector-avatar-3'

# Create your views here.

#  VIEW FUNCTIONS
def home(request):
    '''
    this is where we return a response
    in most cases we  would render a template
    and we'll need some data for that template
    '''
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')

@login_required
def cats_index(request):
    # cats = Cat.objects.all()
    cats = Cat.objects.filter(user=request.user)
    return render(request, 'cats/index.html', {'cats': cats})

# DETIALS
def cats_detail(request, cat_id):
    cat = Cat.objects.get(id=cat_id)
    # Get the toys the cat doesn't have
    toys_cat_doesnt_have = Toy.objects.exclude(id__in = cat.toys.all().values_list('id'))
    feeding_form = FeedingForm()
    return render(request, 'cats/detail.html', {
      'cat': cat, 'feeding_form': feeding_form,
      # Add the toys to be displayed
      'toys': toys_cat_doesnt_have
    })

# FEEDINGS
@login_required
def add_feeding(request, cat_id):
    # pass
    # create the ModelForm using the data in request.POST
    form = FeedingForm(request.POST)
    # validate the form
    if form.is_valid():
        # don't save the form to the db until it
        # has the cat_id assigned
        new_feeding = form.save(commit=False)
        new_feeding.cat_id = cat_id
        new_feeding.save()
    return redirect('detail', cat_id=cat_id)

# ADD TOY
@login_required
def assoc_toy(request, cat_id, toy_id):
    # Note that you can pass a toy's id instead of the whole object
    Cat.objects.get(id=cat_id).toys.add(toy_id)
    return redirect('detail', cat_id=cat_id)

# REMOVE TOY
@login_required
def unassoc_toy(request, cat_id, toy_id):
    Cat.objects.get(id=cat_id).toys.remove(toy_id)
    return redirect('detail', cat_id=cat_id)

# PHOTO
@login_required
def add_photo(request, cat_id):
    # photo-file will be the "name" attribute on the <input type="file">
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
        # if it's present we will create a ref to the boto3 client
        s3 = boto3.client('s3')
        # create a unitque id for each photo file
        # need a unique "key" for S3 / needs image file extension too
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        # funny_cat.png = jdbw7f.png
        # upload the photo file to aws s3
        # just in case something goes wrong
        try:
          #  if successfull
            s3.upload_fileobj(photo_file, BUCKET, key)
            #  take the exchanged url and save it to the  database
            # build the full url string
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            #  1) create a photo instance with photo model and provide cat_id as foreign key value
            # we can assign to cat_id or cat (if you have a cat object)
            photo = Photo(url=url, cat_id=cat_id)
            #  2)
            photo.save()
        except:
            print('An error occurred uploading file to S3')
            return redirect('detail', cat_id=cat_id)
          # print an error message
        return redirect('detail', cat_id=cat_id)


def signup(request):
  error_message = ''
  if request.method == 'POST':
    # This is how to create a 'user' form object
    # that includes the data from the browser
    form = UserCreationForm(request.POST) # in memorey representation
    if form.is_valid():
      # This will add the user to the database
      user = form.save()
      # This is how we log a user in via code
      login(request, user) # pass int he request and the user that neeeds to be logged in
      return redirect('index')
    else:
      error_message = 'Invalid sign up - try again'
  # A bad POST or a GET request, so render signup.html with an empty form
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)


# CLASSES BASED VIEWS
class CatCreate(CreateView):
    model = Cat
    fields = '__all__'
    # or
    # fields = ['name', 'breed', 'description', 'age']
    # success_url = '/cats/'
    # This inherited method is called when a
    # valid cat form is being submitted
    def form_valid(self, form):
        # Assign the logged in user (self.request.user)
        form.instance.user = self.request.user  # form.instance is the cat
        # Let the CreateView do its job as usual
        return super().form_valid(form)


class CatUpdate(LoginRequiredMixin, UpdateView):
    model = Cat
    # Let's disallow the renaming of a cat by excluding the name field!
    fields = ['breed', 'description', 'age']


class CatDelete(LoginRequiredMixin, DeleteView):
    model = Cat
    success_url = '/cats/'

class ToyList(LoginRequiredMixin, ListView):
    model = Toy
    template_name = 'toys/index.html'


class ToyCreate(LoginRequiredMixin, CreateView):
    model = Toy
    fields = '__all__'
    # or
    # fields = ['name', 'breed', 'description', 'age']
    success_url = '/toys/'

class ToyDetail(LoginRequiredMixin, DetailView):
    model = Toy
    template_name = 'toys/detail.html'

class ToyUpdate(LoginRequiredMixin, UpdateView):
    model = Toy
    # Let's disallow the renaming of a Toy by excluding the name field!
    fields = ['name', 'color']


class ToyDelete(LoginRequiredMixin, DeleteView):
    model = Toy
    success_url = '/toys/'


