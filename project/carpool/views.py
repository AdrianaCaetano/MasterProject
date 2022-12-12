from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect   # send message
from django.utils.timezone import datetime, timedelta
import pytz
from django.urls import path  
from django.core.files.storage import FileSystemStorage # save file 
# from django.views.generic import ListView
from django.contrib import messages             # create message when wrong file uploaded
import csv                                      # open and read file

import mycarpool 

from .models import Carpools, Candidates, ParkRide

# Create your views here.
def home(request):
    '''The home webpage view from fucntion home''' 
    PST = pytz.timezone('America/Los_Angeles')
    local_time = datetime.now(PST)
    return render( request, 'carpool/home.html', {'date': local_time} )

def index(request):
    '''Carpools' general information webpage view'''
    carpool_list = Carpools.objects.all()
    context = { 'carpool_list': carpool_list, }
    if(carpool_list):
        last_update = Carpools.objects.values_list('create_date', flat=True).get(pk=1)
        last_update = last_update - timedelta(hours=8)
        print('last_update after', last_update)
        context['last_update'] = last_update
        
        return render( request, 'carpool/carpool_info.html', context )


def generate_csv_file(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=carpools.csv'
    
    # Create a csv writer
    writer = csv.writer(response)

    # Designate The Model
    carpools_all = Carpools.objects.all()

    # Add column headings to the csv file
    writer.writerow(['Carpool ID', 'Driver ID',
                    'Passenger 1 ID', 'Passenger 1 Score', 'Passenger 1 Schedule', 
                    'Passenger 2 ID', 'Passenger 2 Score', 'Passenger 2 Schedule',
                    'Passenger 3 ID', 'Passenger 3 Score', 'Passenger 3 Schedule',
                    ])

    # Loop through carpools and output to the file
    for carpool in carpools_all:
        # print(carpool)
        writer.writerow([carpool.carpool_id, carpool.driver_id, 
                        carpool.passenger_1, carpool.score_1, carpool.schedule_1, 
                        carpool.passenger_2, carpool.score_2, carpool.schedule_2, 
                        carpool.passenger_3, carpool.score_3, carpool.schedule_3,  
                        ])
                        
    return response



def details(request, carpool_id):
    '''Carpool's detail information webpage view'''
    # get carpool
    carpool = get_object_or_404(Carpools, pk= carpool_id)
    # get driver's info
    driver = Candidates.objects.get(pk=carpool.driver_id)
    
    # get passengers' info
    passengers_ids = [ carpool.passenger_1, carpool.passenger_2,carpool.passenger_3]
    passengers_ids = [ pass_id for pass_id in passengers_ids if pass_id != '']
    passengers_lst = Candidates.objects.filter(pk__in = passengers_ids)
    
    context = {'carpool': carpool, 'driver': driver, 'passengers_list': passengers_lst, }

    # Get zips from candidates to find park and ride locations around
    zips_lst = set([cand.zip_code for cand in passengers_lst] )
    if len(zips_lst)>0:
        zips_around_lst = list()
        for zip in zips_lst:
            # print('zip is', type(zip), zip)
            zips_around_lst.append(mycarpool.find_zips_around(location=zip,radius=3))
        around_lst=[]
        if len(zips_around_lst) > 0:
            # print(zips_around_lst)
            if all(isinstance(elem, list) for elem in zips_around_lst):
                # iterate over each list to get zips
                for lst in zips_around_lst:
                    for elem in lst:
                        around_lst.append(elem)
        # print(around_lst)
        around_lst = set(around_lst) # keep only unique values
        # print('around lst',  type(around_lst), len(around_lst), around_lst)
        parkride_lst = ParkRide.objects.filter(zip_code__in= around_lst)
        # print(parkride_lst)
        context['parkride_list']= parkride_lst 

    return render( request, 'carpool/details.html', context )

def upload(request):
    '''The option to upload a file with candidates to carpool
    A valid file upload replaces Candidates database and repopulates Carpool database'''
    context = {}
    if request.method == 'POST':
        uploaded_file = request.FILES['document']

        # save the file into storage
        fs = FileSystemStorage()
        name = fs.save(uploaded_file.name, uploaded_file)
        context['url'] = fs.url(name)
 
        # check file extension
        if not uploaded_file.name.endswith('.csv'):
            messages.warning(request, "This is the wrong file type")
            return HttpResponseRedirect(request.path_info)
        else: 
            # CSV FILE, PROCEED
            # Delete all entries before loading the file into the database
            Candidates.objects.all().delete()
            
            # Open the file and read the data into the database
            file_path = 'media/'+ uploaded_file.name
            file =open(file_path, encoding='utf-8')
            csvreader = csv.reader(file)
            next(csvreader)  # Advance past the header

            try:
                # Read line by line into database
                for fields in csvreader:
                    try: 
                        Candidates.objects.update_or_create(
                            id = fields[0],
                            zip_code = fields[1],
                            role = fields[2],
                            seats = fields[3],
                            gender = fields[4],
                            under_25 = fields[5],
                            undergrad = fields[6],
                            smoker = fields[7],
                            college = fields[8],
                            pref_gender = fields[9],
                            pref_age = fields[10],
                            pref_status = fields[11],
                            pref_nonsmoker = fields[12],
                            M_arr = fields[13],
                            M_dep = fields[14],
                            T_arr = fields[15],
                            T_dep = fields[16],
                            W_arr = fields[17],
                            W_dep = fields[18],
                            R_arr = fields[19],
                            R_dep = fields[20],
                            F_arr = fields[21],
                            F_dep = fields[22],
                            S_arr = fields[23],
                            S_dep =fields[24],
                        )
                    except ValueError:
                        messages.warning(request, "Value Error: Please follow the instructions for all fields")
                        return HttpResponseRedirect(request.path_info) 
            except IndexError:
                messages.warning(request, "File cannot be saved into the database. \nIndex Error: Please follow the instructions for all fields")
                return HttpResponseRedirect(request.path_info)

            # This method doesn't work
            # # make sure data has the standard unicode characters
            # file_data = uploaded_file.read().decode('utf-8')

            # # split data to save into model
            # lines = file_data.split('\n')
            # print('lines',lines)
            # for line in lines:
            #     print('line',line)
            #     fields = line.split(',')
            #     print(fields[0])
            #     ... add all fields
            print('file upload and Candidates database update completed')

            # Clear the Carpool database
            Carpools.objects.all().delete() 

            # Create new carpools with recently added Candidates
            mycarpool.create_carpools()

            print('New Carpools successfuly created')
        # end of else, it is a csv file
    # end of if request
    return render(request, 'carpool/upload.html', context)

def about(request):
    '''The about us webpage view'''
    return render(request,'carpool/about.html')

# class IndexListView(ListView):
#     '''Renders a webpage with a list of all carpools'''
#     model = Carpools

#     def get_context_data(self, **kwargs):
#         context = super(IndexListView, self).get_context_data( **kwargs)
#         return context
        
