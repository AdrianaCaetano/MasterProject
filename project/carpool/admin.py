from django.contrib import admin
from django.urls import path, reverse           # for get_url, upload_csv
from django.shortcuts import render             # for upload_csv 
from django import forms                        # for class CsvImportForm
from django.contrib import messages             # create message when wrong file uploaded
from django.http import HttpResponseRedirect    # return the message


# Register your models here.
from .models import CA_Zip, Candidates, Carpools, ParkRide, Routes

admin.site.register(CA_Zip)
admin.site.register(Candidates)
admin.site.register(Carpools)
admin.site.register(ParkRide)
admin.site.register(Routes)


# All classes/methods below are an attempt to create a file upload inside Admin webpage
class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()

class CarpoolsAdmin(admin.ModelAdmin):
    list_display = ('carpool_id', 'driver_id')
    
    def get_url(self):
        urls = super().get_urls()
        new_urls = [path('upload_csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):
        # upload the file
        if request.method == 'POST':
            csv_file = request.FILES['cvs_upload']
            # check file 
            if not csv_file.name.endswith('.csv'):
                messages.warning(request, "This is the wrong file type")
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode('utf-8')
            # split data to save into model
            csv_data = file_data.split('\n')
            for x in csv_data:
                fields = x.split(',')
                created = Candidates.objects.update_or_create(
                    id = fields[0],
                    # ... add all fields
                )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)
                

        form = CsvImportForm()
        data = { 'form': form }
        return render(request,'admin/upload_csv.html', data)





