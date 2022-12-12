import datetime as dt
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


# Create your models here.

# CA_Zip Table
class CA_Zip(models.Model):
    '''A class to create the CA_Zip database'''
    zip_code = models.PositiveSmallIntegerField(primary_key = True)
    latitude = models.DecimalField(max_digits = 15, decimal_places = 8)
    longitude = models.DecimalField(max_digits = 15, decimal_places = 8)
    state = models.CharField(max_length = 2, default = 'CA')  # only CA zipcodes
    county = models.CharField(max_length = 30)

    def __str__(self):
        return 'Zip Code: %s - %s' % (self.zip_code, self.county)

    

# Candidates Table
class Candidates(models.Model):
    '''A class to create the Candidates database'''
    class Bool(models.IntegerChoices):
        '''A class for integer values of boolean choices'''
        FALSE = 0, _('FALSE')
        TRUE = 1, _('TRUE')

    class Role(models.TextChoices):
        '''A class for string values of possible role char choices'''
        DRIVER = 'D', _('DRIVER')
        PASSENGER = 'P', _('PASSENGER')
        EITHER = 'E', _('EITHER')

    class Gender(models.TextChoices):
        '''A class for string values of possible gender char choices'''
        FEMALE = 'F', _('FEMALE')
        MALE = 'M', _('MALE')
        NON = 'N', _('NON-BINARY')

    class College(models.TextChoices):
        '''A class for string values of possible college choices'''
        COBA = 'COBA', _('COBA')
        CSTEM = 'CSTEM', _('CSTEM')
        CEHHS = 'CEHHS', _('CEHHS')
        CHABSS = 'CHABSS', _('CHABSS')
        UNDECLARED = 'UNDECLARED', _('UNDECLARED')

    HOUR_CHOICES = [(None, '------')] + [(dt.time(hour=x), '{:02d}:00'.format(x)) for x in range(7, 23)]
    # date_list = [dt.time.timedelta(minutes=15*x) for x in range(0, 100)]
    # HOUR_CHOICES = [(None, '------')] + [x.strftime('T%H:%M Z') for x in date_list]

    id = models.PositiveSmallIntegerField(primary_key=True, help_text= 'Student ID')
    zip_code = models.PositiveSmallIntegerField()
    role = models.CharField(max_length = 9 ,choices = Role.choices)
    seats = models.PositiveSmallIntegerField(help_text= 'Available seats')
    gender = models.CharField(max_length=6,choices= Gender.choices)
    under_25 = models.PositiveSmallIntegerField(choices = Bool.choices)
    undergrad = models.PositiveSmallIntegerField(choices = Bool.choices) 
    smoker = models.PositiveSmallIntegerField(choices = Bool.choices)
    college = models.CharField(max_length= 10, choices = College.choices)
    pref_gender = models.PositiveSmallIntegerField(choices = Bool.choices, null=True, blank=True, verbose_name= 'Prefer same gender?')
    pref_age = models.PositiveSmallIntegerField(choices = Bool.choices, null=True, blank=True, verbose_name= 'Prefer same age group?')
    pref_status = models.PositiveSmallIntegerField(choices = Bool.choices, null=True, blank=True, verbose_name= 'Prefer same school status? (Undergrad/Grad)')
    pref_nonsmoker = models.PositiveSmallIntegerField(choices = Bool.choices, null=True, blank=True, verbose_name= 'Prefer non-smoker?')
    M_arr = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Monday Arrival')
    M_dep = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Monday Departure') 
    T_arr = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Tuesday Arrival') 
    T_dep = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Tuesday Departure') 
    W_arr = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Wednesday Arrival') 
    W_dep = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Wednesday Departure') 
    R_arr = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Thursday Arrival') 
    R_dep = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Thursday Departure') 
    F_arr = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Friday Arrival') 
    F_dep = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Friday Departure') 
    S_arr = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Saturday Arrival') 
    S_dep = models.TimeField(choices= HOUR_CHOICES, null=True, blank=True, verbose_name = 'Saturday Departure') 

    def __str__(self):
        characteristics = self.gender + ', ' + self.college + ', '
        if (self.under_25):
            characteristics += 'under 25, '
        else:
            characteristics += '25 or above, '

        if (self.undergrad):
            characteristics += 'undergraduate, '
        else:
            characteristics += 'graduate, ' 

        if (self.smoker):
           characteristics += 'smoker.'
        else:
            characteristics += 'non-smoker.' 

        return 'ID: %d, Zip Code: %d, Profile: %s' % (self.id, self.zip_code, characteristics)



# Carpool Table
class Carpools(models.Model):
    '''A class to create a database to hold carpools'''
    class Direction(models.TextChoices):
         '''Class for string values of possible char directions'''
         ROUND_TRIP = 'RT', _('round-trip')
         OUTBOUND = 'O', _('outbound')
         RETURN = 'R',  _('return')
    
    class Schedule(models.TextChoices):
        '''Class for string values of possible schedules'''
        WEEK = 'week',_('MTWRFS')  # all weekdays
        MWF = 'MWF', _('MWF')      # Monday/Wednesday/Friday
        TR = 'TR', _('TR')         # Tuesday/Thrusday
        M = 'M', _('M')            # Monday
        T = 'T', _('T')            # Tuesday
        W = 'W', _('W')            # Wednesday
        R = 'R', _('R')            # Thursday
        F = 'F', _('F')            # Friday
        S = 'S', _('S')            # Saturday   

    carpool_id = models.AutoField(primary_key=True)
    driver_id = models.PositiveSmallIntegerField()
    passenger_1 = models.PositiveSmallIntegerField(blank= True, null= True,)
    score_1 = models.CharField(max_length= 3, blank= True, null= True,)
    schedule_1 = models.CharField(max_length= 10, choices= Schedule.choices, blank= True, null= True,)
    passenger_2 = models.PositiveSmallIntegerField(blank= True, null= True,)
    score_2 = models.CharField(max_length= 3, blank= True, null= True,)
    schedule_2 = models.CharField(max_length= 10, choices= Schedule.choices, blank= True, null= True,)
    passenger_3 = models.PositiveSmallIntegerField(blank= True, null= True,)
    score_3 = models.CharField(max_length= 3, blank= True, null= True,)
    schedule_3 = models.CharField(max_length= 10, choices= Schedule.choices, blank= True, null= True,)
    direction = models.CharField(max_length= 10, choices= Direction.choices, default = Direction.ROUND_TRIP)
    create_date = models.DateTimeField('Creation Date', default= now)
    
    
    def __str__(self):
        origin = Candidates.objects.get(id=self.driver_id).zip_code
        seats = Candidates.objects.get(id=self.driver_id).seats
        passengers = '['
        if self.passenger_1:
            passengers += str(self.passenger_1) + ', '
        if self.passenger_2:
            passengers += str(self.passenger_2) + ', '
        if self.passenger_3:
            passengers += str(self.passenger_3) 
        passengers += ']'

        return 'Carpool: %d, Origin: %s, Driver: %d, Seats: %d, Passenger(s): %s' % (self.carpool_id, origin, self.driver_id, seats, passengers )


    
# Park & Ride Table
class ParkRide(models.Model):
    '''A class to create a Park and Ride database'''
    lot_id = models.IntegerField(primary_key = True)
    zip_code = models.PositiveSmallIntegerField()
    district = models.CharField(max_length = 3)
    county = models.CharField(max_length = 3)
    city = models.CharField(max_length = 22)
    name = models.CharField(max_length = 60)
    address = models.CharField(max_length = 120)
    latitude = models.DecimalField(max_digits = 15, decimal_places = 8)
    longitude = models.DecimalField(max_digits = 15, decimal_places = 8)

    def __str__(self):
        return 'Park & Ride at %s: %s - %s, %s' %(self.zip_code, self.name, self.address, self.city)



# Routes Table
class Routes(models.Model):
    '''A class to create Routes database'''
    origin_id = models.PositiveSmallIntegerField(primary_key=True)     # origin zip code
    s_route_dist = models.TextField()
    s_route_time = models.TextField()
    travel_time = models.CharField(max_length = 10) # string HH:MM:SS
    travel_distance = models.DecimalField(max_digits = 7, decimal_places = 2)
    zips_on_route = models.CharField(max_length = 4000) # list of zips on the route

    def __str__(self):
        return 'Route Origin: %s, Route Path: %s' % (self.origin_id, self.zips_on_route)


    