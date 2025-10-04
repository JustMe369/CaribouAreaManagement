@echo off
echo Creating Caribou Coffee Area Manager Dashboard Project...
echo.

REM Navigate to the Desktop and create the main project folder
cd /d %USERPROFILE%\Desktop
mkdir CaribouProject
cd CaribouProject

REM Create the virtual environment and activate it (We'll do this manually later for safety)
echo Step 1/5 - Creating project structure...

REM Create the main Django project
django-admin startproject caribou_dashboard .

REM Create the apps
python manage.py startapp checklist
python manage.py startapp users

echo Step 2/5 - Creating template directories...
REM Create directories for templates
mkdir templates
mkdir templates\registration
mkdir templates\checklist
mkdir templates\users

echo Step 3/5 - Creating static files directory...
REM Create directory for static files (CSS, JS, Images)
mkdir static
mkdir static\css
mkdir static\js
mkdir static\images

echo Step 4/5 - Writing configuration and model files...

REM 1. Update settings.py to include the apps and template dir
echo Appending app and directory configurations to settings.py...
(
echo INSTALLED_APPS = [
echo     'django.contrib.admin',
echo     'django.contrib.auth',
echo     'django.contrib.contenttypes',
echo     'django.contrib.sessions',
echo     'django.contrib.messages',
echo     'django.contrib.staticfiles',
echo     'checklist',
echo     'users',
echo ]
) >> caribou_dashboard\settings.py
echo Adding template directory to settings.py...
(
echo.
echo import os
echo TEMPLATES = [
echo     {
echo         'BACKEND': 'django.template.backends.django.DjangoTemplates',
echo         'DIRS': [os.path.join(BASE_DIR, 'templates')],
echo         'APP_DIRS': True,
echo         'OPTIONS': {
echo             'context_processors': [
echo                 'django.template.context_processors.debug',
echo                 'django.template.context_processors.request',
echo                 'django.contrib.auth.context_processors.auth',
echo                 'django.contrib.messages.context_processors.messages',
echo             ],
echo         },
echo     },
echo ]
) >> caribou_dashboard\settings.py

echo Adding static files directory to settings.py...
(
echo.
echo STATIC_URL = '/static/'
echo STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
) >> caribou_dashboard\settings.py

REM 2. Create the models.py file for the checklist app
echo Creating models.py for checklist app...
(
echo from django.db import models
echo from django.contrib.auth.models import User
echo.
echo class Store(models.Model):
echo     name = models.CharField(max_length=100)
echo     address = models.TextField()
echo     manager_name = models.CharField(max_length=100, blank=True)
echo.
echo     def __str__(self):
echo         return self.name
echo.
echo class AreaManagerVisit(models.Model):
echo     store = models.ForeignKey(Store, on_delete=models.CASCADE)
echo     manager = models.ForeignKey(User, on_delete=models.CASCADE)
echo     date = models.DateField(auto_now_add=True)
echo     month = models.CharField(max_length=20)
echo     time = models.TimeField(auto_now_add=True)
echo     overall_score = models.IntegerField(blank=True, null=True)
echo     notes = models.TextField(blank=True)
echo.
echo     def __str__(self):
echo         return f"Visit to {self.store.name} on {self.date}"
echo.
echo class ChecklistItem(models.Model):
echo     visit = models.ForeignKey(AreaManagerVisit, on_delete=models.CASCADE, related_name='items')
echo     category = models.CharField(max_length=100)
echo     question_number = models.IntegerField()
echo     question_text = models.TextField()
echo     answer = models.BooleanField()
echo     comment = models.TextField(blank=True)
echo.
echo     def __str__(self):
echo         return f"{self.category} - Q{self.question_number}"
echo.
echo class ActionPlanItem(models.Model):
echo     STATUS_CHOICES = [
echo         ('open', 'Open'),
echo         ('in_progress', 'In Progress'),
echo         ('closed', 'Closed'),
echo     ]
echo     visit = models.ForeignKey(AreaManagerVisit, on_delete=models.CASCADE, related_name='action_items')
echo     what = models.TextField()
echo     who = models.CharField(max_length=100)
echo     timeframe = models.DateField()
echo     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
echo     remarks = models.TextField(blank=True)
echo.
echo     def __str__(self):
echo         return f"Action: {self.what}"
) > checklist\models.py

REM 3. Create the admin.py file to register models
echo Creating admin.py for checklist app...
(
echo from django.contrib import admin
echo from .models import Store, AreaManagerVisit, ChecklistItem, ActionPlanItem
echo.
echo admin.site.register(Store)
echo admin.site.register(AreaManagerVisit)
echo admin.site.register(ChecklistItem)
echo admin.site.register(ActionPlanItem)
) > checklist\admin.py

REM 4. Create a simple view and URL for the homepage
echo Creating a welcome view and URL...
(
echo from django.http import HttpResponse
echo.
echo def home_page(request):
echo     return HttpResponse^("<h1>Welcome to Caribou Coffee Dashboard</h1><p>Your project is set up successfully!</p>"^)
) > users\views.py

(
echo from django.urls import path
echo from . import views
echo.
echo urlpatterns = [
echo     path('', views.home_page, name='home'),
echo ]
) > users\urls.py

REM 5. Update the main urls.py to include the app's URLs
echo Updating main urls.py...
(findstr /v "urlpatterns" caribou_dashboard\urls.py > new_urls.txt) && (move /y new_urls.txt caribou_dashboard\urls.py >nul)
(
echo from django.contrib import admin
echo from django.urls import path, include
echo.
echo urlpatterns = [
echo     path('admin/', admin.site.urls),
echo     path('', include('users.urls')),
echo     path('checklist/', include('checklist.urls')),
echo ]
) >> caribou_dashboard\urls.py

REM 6. Create placeholder files for the checklist app
echo Creating placeholder views and urls for checklist app...
(
echo from django.http import HttpResponse
echo.
echo def checklist_index(request):
echo     return HttpResponse^("Checklist App Index"^)
) > checklist\views.py

(echo from django.urls import path; echo from . import views; echo urlpatterns = [path('', views.checklist_index, name='checklist_index'),] ) > checklist\urls.py

REM 6. Create a basic login template
echo Creating a login template...
(
echo ^<!DOCTYPE html^>
echo ^<html^>
echo ^<head^>
echo     ^<title^>Login - Caribou Coffee^</title^>
echo     ^<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"^>
echo ^</head^>
echo ^<body^>
echo     ^<div class="container mt-5"^>
echo         ^<div class="row justify-content-center"^>
echo             ^<div class="col-md-6"^>
echo                 ^<div class="card"^>
echo                     ^<div class="card-header"^>
echo                         ^<h3 class="text-center"^>Caribou Coffee Dashboard^</h3^>
echo                         ^<p class="text-center"^>Please log in^</p^>
echo                     ^</div^>
echo                     ^<div class="card-body"^>
echo                         ^<form method="post"^>
echo                             {% csrf_token %}
echo                             {{ form.as_p }}
echo                             ^<button type="submit" class="btn btn-primary w-100"^>Login^</button^>
echo                         ^</form^>
echo                     ^</div^>
echo                 ^</div^>
echo             ^</div^>
echo         ^</div^>
echo     ^</div^>
echo ^</body^>
echo ^</html^>
) > templates\registration\login.html

echo Step 5/5 - Finalizing setup...

echo.
echo Project created successfully!
echo.
echo NEXT STEPS:
echo 1. Double-check the file 'caribou_dashboard/settings.py'. The script might have appended to the end.
echo    You may need to manually integrate the INSTALLED_APPS, TEMPLATES, and STATIC settings into the existing code.
echo 2. Run the following commands in this directory:
echo    python -m venv caribou_env
echo    caribou_env\Scripts\activate
echo    pip install django
echo    python manage.py makemigrations
echo    python manage.py migrate
echo    python manage.py createsuperuser
echo    python manage.py runserver
echo.
pause