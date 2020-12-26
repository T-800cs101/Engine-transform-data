#author gregori povolotslki
#Project that create one of etl processes (transformation process)

import getpass
import pprint
import openpyxl
import pandas as pd
import numpy as np
import os, sys, re
import itertools
import logging
import sxl
from django.utils.timezone import get_current_timezone
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, HttpResponseRedirect, reverse, redirect
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.datastructures import MultiValueDictKeyError
from flask import render_template
from pandas._libs import json
from xlrd import XLRDError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import LoginForm, InputForm
from django.db import connection, ProgrammingError,DataError
from django.apps import apps
from django.core.exceptions import MultipleObjectsReturned
from django.core.files.storage import FileSystemStorage
from django.forms import formset_factory
from django.core.files.storage import default_storage
from datetime import datetime
from json import JSONEncoder
from django.template import loader
from django import template
from . models import  Log_Reporting, Log_Mapping_Performe, Dimensions, \
    Mapping_Rules,  Mapping_Table, Reporting_Event,Mapping_Sets,  Reporting_Period, \
    Entity, Konto, Partner, Movement_Type, Investe, Document_Type,Imported_Data, Mapping_Data, Mapping_Rules_Main, Betrag



# Be careful of IndexError: list index out of range
logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s- %(message)s')
logging.debug('Start of Program')

# Create your views here.
list_default_dim = ['Reporting Event', 'Reporting Period', 'Entity', 'Konto', 'Partner', 'Movement Type', 'Investe', 'Document Type']
list_custom_dim = ['Custom 1', 'Custom 2', 'Custom 3', 'Custom 4']
list_custom_dim_export = ['custom_1', 'custom_2', 'custom_3', 'custom_4']
list_mapping_t = ['mapping t 1','mapping t 2','mapping t 3','mapping t 4','mapping t 5','mapping t 6','mapping t 7','mapping t 8','mapping t 9','mapping t 10']
list_betrag = ['Value in LC','Value in GC','Value in TC','Quantity']
list_tbl_not_to_export = ['Dimensions','Betrag','Mapping Rules Main', 'Mapping Rules setName','Master Data', 'Mapping Data',
                          'Mapping Sets','Log Reporting', 'Log Mapping Performe','Mapping Table','Mapping Rules']

dimensions_list = Dimensions.objects.values_list('id','dimensionName','new_name')
numpy_array_dim = np.array(list(dimensions_list))
username = getpass.getuser()
#create directory to save files
path = 'C:\\Users\\'+username+'\Desktop\\Engine'

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

sq = User.objects.all()

@permission_required('engine_app.admin', login_url='home')
@login_required(login_url='user_login')
def admin(request):# admin function. can create and delete users.
    obj = User.objects.all()
    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')
        if 'delete' in request.POST:
            if 'vehicle1' in request.POST:
                id = request.POST.getlist('vehicle1')
                logging.debug(id)
                logging.debug('checked ' + str(id[0]))
                try:
                    logging.debug('try')
                    for i in range(len(id)):
                        with connection.cursor() as cursor:  # delete user
                            cursor.execute('''DELETE FROM auth_user WHERE id = ''' + id[i])
                            messages.success(request, "User with id " + str(id[i]) + "was deleted")
                except ():
                    messages.warning(request, "User with id " + str(id[i]) + " cant be deleted")

        if 'submit' in request.POST: #create user
            name = request.POST.get('name')
            username = request.POST.get('username')
            pw = request.POST.get('pw')
            admin = request.POST.get('admin')
            logging.debug(name)
            logging.debug(username)
            logging.debug(pw)
            logging.debug(admin)
            user = User.objects.create_user(str(username), '', str(pw))
            if admin == 'Yes':
                user.is_superuser = True
            user.first_name = str(name)
            user.save()
    return render(request, 'admin.html', {'obj': obj })


def user_login(request): #login logout
    logging.debug('login')
    user_1 = User.objects.values_list('username','password')#get User data from User model
    n_arr = np.array(list(user_1))
    logging.debug(user_1)
    logging.debug(user_1[0])
    if request.method == 'POST':
        logging.debug('post')
        if 'btn_login' in request.POST:
            username = request.POST.get('username')#get username from html form
            password = request.POST.get('password')#get password from html form
            logging.debug(username)
            logging.debug(password)
            user = authenticate(request, username=username,password=password)#check if login data excist in DB
            if user is not None:#if user is in DB allow user to enter to Web tool end open 'home' page
                login(request, user)
                return redirect('home')
            else:#dont allow the entry
                messages.info(request, 'Username OR Password is inccorect')
                return redirect('user_login')

    context = {}
    return render(request, 'login.html', context)




@login_required(login_url='user_login')# all program function can be used by autorized users
def home(request):
    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')
    return render(request, 'home.html')

@login_required(login_url='user_login')
def import_files(request): #import data that must be transformed
    #Attributes
    f = ''
    df = ''
    df1 = ''
    comment = ''
    sheet = ''
    list_relation= ['None']
    list_import_df = []
    list_import_dim = []
    now = datetime.now()
    # Objects
    obj = Log_Reporting.objects.all().order_by('timestamp')
    event = Reporting_Event.objects.all()
    period = Reporting_Period.objects.all()
    obj_dim = Dimensions.objects.all().order_by('id')
    obj_b = Betrag.objects.all().order_by('id')

    #check the item to delete and delete them from log table
    if request.user.is_authenticated:
        user = request.user.username
        user_id = request.user.id
        logging.debug(user)
        logging.debug(user_id)
    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')
        if 'delete_log' in request.POST:
            if 'check' in request.POST:
                id = request.POST.getlist('check')
                logging.debug('checked '+str(id[0]))
                try:
                    logging.debug('try')
                    for i in range(len(id)):
                        a = Log_Reporting.objects.get(id=str(id[i]))
                        logging.debug(a.event)
                        logging.debug(a.period)
                        with connection.cursor() as cursor:  # add new column to db table
                            logging.debug('''DELETE FROM engine_app_imported_data WHERE reporting_event = \'''' + a.event + '''\' AND reporting_period = \'''' + a.period + '''\'''')
                            cursor.execute('''DELETE FROM engine_app_imported_data WHERE reporting_event = \'''' + a.event + '''\' AND reporting_period = \'''' + a.period + '''\'''')
                            cursor.execute('''DELETE FROM engine_app_log_reporting WHERE id = ''' + id[i])
                            messages.success(request, "Item with id " +str(id[i]) + "was deleted")
                except ():
                    messages.warning(request, "Item with id " +str(id[i]) +" cant be deleted")
#-----------------------------------------------------------------------------------------------------------------------#
        if 'import_f' in request.POST and request.FILES['test']:#getting the file  to read and browse in gui
            logging.debug('firs import')
            import_f = request.POST.get('import_f')
            logging.debug(import_f)
            event = request.POST.get('sel_event')
            period = request.POST.get('sel_period')
            comment = request.POST.get('comment')
            sheet = request.POST.get('sheet_name')
            f = request.FILES['test']
            logging.debug(sheet)
            file_name = default_storage.save(f.name, f)
            file = default_storage.open(file_name)
            #df = pd.read_excel(file, "Data", header = 0).iloc[:100]#read only 10 rows to browse the file
            wb = sxl.Workbook(file)

            try:
                ws = wb.sheets[str(sheet)]  # this gets the first sheet
                data = ws.head(100)
                logging.debug(data)
                file.close()
                logging.debug(3)
                np1 = np.array(data)
                logging.debug(np1)
                df = pd.DataFrame(np1, columns=np1[0])
                logging.debug(df)
                df1 = df.to_records(index=False)
                logging.debug('--------')
                tempo = list_relation + list(obj_dim)

                logging.debug(event)
                logging.debug(period)
                logging.debug(comment)
                logging.debug(df)
                logging.debug(df1[1:])
            except KeyError:
                messages.error(request,"Error!Sheet name is wrong. Check your Import file.")
                file.close()
                event = Reporting_Event.objects.all()
                period = Reporting_Period.objects.all()

        if 'import_t' in request.POST: #in gui selecting relationship between dimensions and file columns
            logging.debug('import')
            v = request.POST.getlist('index_df_col')# getting index of columns names
            k = request.POST.getlist('dim_option')#getting dimensions
            p = request.POST.getlist('df_names')#geting columns names
            f = request.POST.get('f')#we need also to get file name that was loaded.
            event = request.POST.get('event')
            period = request.POST.get('period')
            comment = request.POST.get('comment')
            sheet = request.POST.get('sheet_name') #sheet name
            v_p_k = np.column_stack((v,p,k))#set 3 list to one to save to compare it and save needed data to model
            logging.debug(sheet)
            logging.debug(v_p_k)
            logging.debug(numpy_array_dim)
            logging.debug(v_p_k[1,2])
            for i in range(len(v_p_k)):
                if v_p_k[i,2] == '-none-':#if none do nothing
                    logging.debug('Empty Select field')
                if v_p_k[i,2] in list_default_dim:#if item in dim list add it to lists
                    logging.debug('Not Empty Select field 1')
                    list_import_df.append(v_p_k[i,1])
                    list_import_dim.append(v_p_k[i,2])
                if v_p_k[i, 2] not in list_default_dim and v_p_k[i, 2]  in list_custom_dim and v_p_k[i,2] != '-none-':
                        logging.debug('Not Empty Select field 2')
                        list_import_df.append(v_p_k[i, 1])
                        list_import_dim.append(v_p_k[i, 2])
                if v_p_k[i, 2] not in list_default_dim and v_p_k[i, 2]  in list_betrag and v_p_k[i,2] != '-none-':
                        logging.debug('Not Empty Select field 2_1')
                        list_import_df.append(v_p_k[i, 1])
                        list_import_dim.append(v_p_k[i, 2])
                if v_p_k[i, 2] not in list_default_dim and v_p_k[i, 2] not in list_custom_dim and v_p_k[i, 2] not in list_betrag and v_p_k[i,2] != '-none-':
                    logging.debug('Not Empty Select field 3')
                    result = np.where(numpy_array_dim == v_p_k[i, 2])#find index of item
                    logging.debug(result)
                    list_import_df.append(v_p_k[i, 1])#
                    list_import_dim.append(numpy_array_dim.item(int(result[0]),int(result[1]-1)))#add item to list of dim with cordinates from result
            list_import_dim.append('Reporting Event')
            list_import_dim.append('Reporting Period')
            logging.debug(list_import_df)
            logging.debug('list_import_dim')
            logging.debug(list_import_dim)
#the point is to open the imported file in the end of logik to save time for posible mistake by chosing relations
            if 'Entity' in list_import_dim and 'Konto' in list_import_dim and ('Value in LC' in list_import_dim or 'Value in GC' in list_import_dim
                            or 'Value in TC' in list_import_dim  or 'Quantity' in list_import_dim ):
                file = default_storage.open(f)  # opening the uploaded file
                table_name = 'imported_data'
                df = pd.read_excel(file, sheet, header=0)
                #need to add progress bar
                data = df[
                    df.columns.intersection(list_import_df)]  # get from dataFrame only needed columns from post request
                data = data.where(pd.notnull(data), None)
                logging.debug(data)
                logging.debug("--------------------------------")
                data['Event'] = event
                data['Period'] = period
                data_list = data.values.tolist()#convert df to values list
                logging.debug(np.asarray(data))
                logging.debug("--------------------------------")
                logging.debug(format(data_list))
                for i in data_list:
                    logging.debug(i)
                logging.debug("--------------------------------")
                log_data = Log_Reporting.objects.filter(event=event, period=period)
                logging.debug(len(log_data))
                try:
                    if len(log_data) > 0:
                        obj_old_data = Imported_Data.objects.filter(reporting_event=event, reporting_period=period)
                        obj_old_data.delete()
                        logging.debug('deleted old data')
                        log_data.delete()
                    insert_in_db(list_import_dim,data_list,table_name)#function to insert data to data base(functions are on bottom)
                except(ProgrammingError):
                    messages.error(request,'ERROR!Select option cant be chosen twice')
                file.close()  # before delting the file we need to close it
                default_storage.delete(f)  # delete file
#-----------------------------------------------------------------------------------------------------------------------------#
                user_log = Log_Reporting.objects.create(
                    event=event,
                    period=period,
                    file=str(f),
                    timestamp=now.strftime("%Y-%m-%d_%H:%M:%S"),
                    user=request.user,
                    comment=str(comment)
                )
                user_log.save()
                logging.debug(event)
                event = Reporting_Event.objects.all()
                period = Reporting_Period.objects.all()
                df = pd.DataFrame()
            else:
                event = Reporting_Event.objects.all()
                period = Reporting_Period.objects.all()
                default_storage.delete(f)  # delete file
                df = pd.DataFrame()
                messages.error(request,"Error! Required Dimensions Entity, Konto and one of Value option was not chosen.")

###############################################################################################################################



    data = {
        'obj': obj,
        'event': event,
        'period':period,
        'df':df1[1:],
        'df_head':list(df),
        'obj_dim': obj_dim,
        'obj_b':obj_b,
        'f':f,
        'sheet': sheet,
        #'event':event,
        #'period':period,
        'comment':comment

    }
    logging.debug(10)
    return render(request, 'import_files.html', data)

@login_required(login_url='user_login')
def import_mapping_table(request):# import mapping data
    f = ''
    df = ''
    df1 = ''
    dim = ''
    dimension = ''
    list_header = []
    list_import_df = []
    list_import_dim = []
    obj_dim_name = Mapping_Data.objects.all().order_by('id')
    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')
        if 'dimension' in request.POST:
            logging.debug('dimension----------')
            dimension = request.POST.get('dimension')
            logging.debug(dimension)
        try:
            if 'import' in request.POST and request.FILES['file_im']:
                f = request.FILES['file_im']
                option = request.POST.get('dim_name_im')
                dimension = option
                logging.debug(option)
                if option != ['']:
                    logging.debug(str(option) + ' select options')
                    dim = conver_right_formt_of_tbl_name(option)
                    file_name = default_storage.save(f.name, f)
                    try:
                        df = pd.read_excel(f, "Sheet1", header=0, nrows=10)  # read only 10 rows to browse the file

                        np1 = np.array(df)
                        try:
                            df["code"] = df.code.map("{:04}".format)
                        except(AttributeError):
                            logging.debug('format works only with field code')
                        df1 = df.to_records(index=False)

                        logging.debug('--------')
                        logging.debug(df1)
                        logging.debug(dim)
                        cursor = connection.cursor()
                        sql_string = '''select column_name from information_schema.columns where table_name='engine_app_''' + dim.lower() + '''' '''
                        cursor.execute(sql_string)
                        sql_header = cursor.fetchall()
                        logging.debug(sql_header)
                        list_header = np.array([str(x) for x, in sql_header])
                        logging.debug(list_header)
                    except(XLRDError):
                        default_storage.delete(file_name)  # delete file
                        messages.error(request, 'The Sheet name of your file must be \'Sheet1\' ')
                else:
                    messages.error(request, 'Error!The destination table was not chosen')

        except(MultiValueDictKeyError):
            messages.error(request, "ERROR! Choose the file and destination table please")
        if 'submit' in request.POST:
            logging.debug('import')
            v = request.POST.getlist('index_df_col')  # getting index of columns names
            k = request.POST.getlist('dim_option')  # getting dimensions
            p = request.POST.getlist('df_names')  # geting columns names
            f = request.POST.get('f')  # we need also to get file name that was loaded.
            tbl_n = request.POST.get('dim')
            logging.debug(tbl_n)
            cursor = connection.cursor()
            sql_string = '''select column_name from information_schema.columns where table_name='engine_app_''' + tbl_n.lower() + '''' '''
            cursor.execute(sql_string)
            sql_header = cursor.fetchall()
            logging.debug(sql_header)
            list_header = np.array([str(x) for x, in sql_header])
            new_list_h = np.array(list_header)
            v_p_k = np.column_stack(
                (v, p, k))  # set 3 list to one to save to compare it and save needed data to model
            logging.debug(v_p_k)
            for i in range(len(v_p_k)):
                if v_p_k[i, 2] == '-none-':  # if none do nothing
                    logging.debug('Empty Select field')

                if v_p_k[i, 2] in new_list_h[1:]:  # if item in dim list add it to lists
                    logging.debug('Not Empty Select field')
                    list_import_df.append(v_p_k[i, 1])
                    list_import_dim.append(v_p_k[i, 2])
                if v_p_k[i, 2] not in new_list_h[1:] and v_p_k[i, 2] in list_custom_dim and v_p_k[i, 2] != '-none-':
                    list_import_df.append(v_p_k[i, 1])
                    list_import_dim.append(v_p_k[i, 2])
            logging.debug(list_import_df)
            logging.debug(list_import_dim)
            # the point is to open the imported file in the end of logik to save time for posible mistake by chosing relations
            file = default_storage.open(f)  # opening the uploaded file
            table_name = tbl_n.lower()
            df = pd.read_excel(file, "Sheet1", header=0)
            try:
                df["code"] = df.code.map("{:04}".format)
            except(AttributeError):
                logging.debug('format works only with field code')
            # need to add progress bar
            data = df[
                df.columns.intersection(list_import_df)]  # get from dataFrame only needed columns from post request
            data_list = data.values.tolist()  # convert df to values list
            print(data)
            print(data_list)
            try:
                with connection.cursor() as cursor:  # add new column to db table
                    cursor.execute('''TRUNCATE TABLE engine_app_''' + tbl_n.lower() + ''' RESTART IDENTITY;''')
                    logging.debug('delete all items')
                    insert_in_db(list_import_dim, data_list,
                                 table_name)  # function to insert data to data base(functions are on bottom)
                    file.close()  # before deleting the file we need to close it
                    default_storage.delete(f)  # delete file
            except(DataError):
                file.close()
                messages.error(request,
                               "Error!Code field is required field and must compare the format of four digits and no double select of option is allowed")
            except(ProgrammingError):
                file.close()  # before deleting the file we need to close it
                messages.error(request, 'Error!Multiple selection of option fields or no option was selected')


    context = {

        'obj_dim_name': obj_dim_name,
        'df1': df1,
        'df_head': list(df),
        'list_header': list_header[1:],
        'dim': dim,
        'f': f,
        'dimension':dimension
    }
    return render(request, 'import_mt.html', context)

@login_required(login_url='user_login')
def brows_mapping_table(request):
    obj_dim_name = Mapping_Data.objects.all().order_by('id')
    list_np = ''
    var_db = ''
    option = ''
    list_var = []
    list_np_dt = []
    i = 0
    var_template = ''
    now = datetime.now()

    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')
        if 'dimension' in request.POST:
            logging.debug('select mt')
            option = request.POST.get('dimension')  # get the selected option and set it as table name
            logging.debug(option)
            temporar = str(option)
            b = temporar.replace(' ', '_')  # 1.1 replace char to set right format of db table name
            var_db = ''.join(
                [i for i in b if i or i == '_'])  # 1.2 replace char to set right format of db table name
            var_template = ''.join(
                [i for i in temporar if
                 i or i == ' '])  # replace to set right format for dim. name in template

            if str(option) not in list_default_dim:
                p = Mapping_Data.objects.filter(new_name=str(option)).values('id')  # change custom 1 to attribute!!!!
                a = str(p)
                logging.debug(str(a) + ' ---------')
                key = int(''.join([i for i in a if i.isdigit()]))
                c = Mapping_Data.objects.get(id=key)
                g = c.name
                dimension_name = g  # so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                dim_name = g
                print(str(dim_name) + ' not in both lists')
                var_db = str(dim_name).replace(' ','_')
            if str(option) not in list_default_dim and str(option) in list_custom_dim:
                # dim_name = g#so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                print(str(dim_name) + ' in custom list')
                p = Mapping_Data.objects.filter(name=str(dim_name)).values(
                    'id')  # change custom 1 to attribute!!!!
                a = str(p)
                print(a)
                key = int(''.join([i for i in a if i.isdigit()]))
                c = Dimensions.objects.get(id=key)
                g = c.new_name
                dimension_name = g  # so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                print(g)
                var_db = str(dimension_name).replace(' ', '_')
            else:
                var_db = var_db
            logging.debug(var_db)
            cursor = connection.cursor()
            # SQL code to return columns from table
            sql_data_type = '''SELECT COLUMN_NAME,CHARACTER_MAXIMUM_LENGTH,NUMERIC_PRECISION
                                                            FROM INFORMATION_SCHEMA.COLUMNS
                                                                WHERE TABLE_NAME ='engine_app_''' + var_db.lower() + '''' 
                                                                AND COLUMN_NAME <> 'id';'''

            cursor.execute(sql_data_type)
            sql_data_t = cursor.fetchall()
            list_np_dt = np.array(sql_data_t)
            logging.debug('list_np_dt-----------')
            logging.debug(list_np_dt)
            # SQL code to return columns from table
            sql_string = '''select * from engine_app_''' + var_db.lower()
            print(sql_string)
            sql_string_header = '''select column_name from information_schema.columns where table_name='engine_app_''' + var_db.lower() + '''' '''
            cursor.execute(sql_string)
            sql_columns = cursor.fetchall()
            cursor.execute(sql_string)
            list_np = np.array(sql_columns)
            if (len(list_np) > 0):
                list_np = np.delete(list_np, [0], axis=1)
                logging.debug(list_np)
            cursor.execute(sql_string_header)
            sql_columns_header = cursor.fetchall()
            list_header = np.array(sql_columns_header)
            logging.debug('-------------')
            logging.debug(list_header)
            for i in range(list_header.__len__()):
                logging.debug(list_header.item(i))
                if (list_header.item(i) != 'id'):
                    list_var.append(list_header.item(i))
            logging.debug('----------')
            logging.debug(list_var)

        if 'delete' in request.POST:
            logging.debug('delete')
            if 'check' in request.POST:
                id = request.POST.getlist('check')
                dim = request.POST.get('dim')
                list = request.POST.getlist('list_np')
                logging.debug(dim)
                logging.debug(len(list))
                logging.debug('checked ' + str(id[0]))
                logging.debug(id)
                try:
                    logging.debug('try')
                    logging.debug('length of list ' + str(len(id)))
                    if len(list) > len(id):
                        for i in range(len(id)):
                            logging.debug(id[i])
                            with connection.cursor() as cursor:  # add new column to db table
                                cursor.execute(
                                    '''DELETE FROM engine_app_''' + dim.lower() + ''' WHERE code = \'''' + id[
                                        i] + '''' ''')
                                logging.debug('delete item')
                                messages.success(request, "Item with id " + str(id[i]) + " was deleted")
                    else:  # when all data must be deleted.delete all data and reset id increment to 0
                        with connection.cursor() as cursor:  # add new column to db table
                            cursor.execute('''TRUNCATE TABLE engine_app_''' + dim.lower() + ''' RESTART IDENTITY;''')
                            logging.debug('delete all items')
                            messages.success(request, "All item was deleted")
                except ():
                    messages.warning(request, "Item with id " + str(id[i]) + " cant be deleted")
        # -----------------------------------------------------------------------------------------------------------------------#
        if 'save' in request.POST:  #
            logging.debug('save')
            tbl = request.POST.getlist('td_table')
            lst_h = request.POST.getlist('list_header')
            old_data = request.POST.getlist('td_tbl_old')
            old_data_1 = request.POST.getlist('td_table_old')
            dim = request.POST.get('dim')
            length = request.POST.getlist('length')
            d_t = request.POST.getlist('d_t')
            logging.debug(tbl)
            logging.debug(lst_h)
            logging.debug(dim)
            logging.debug(old_data)
            logging.debug(old_data_1)
            logging.debug(len(tbl))
            logging.debug(len(lst_h))
            try:
                increment = int(len(old_data) / len(lst_h))  #
                logging.debug(increment)
                f = np.array(old_data).reshape(increment, len(lst_h))
                e = [i[0] for i in f]
                logging.debug(
                    e)  # list with 'code' field only .this must be compared with new iput whenn old input data is disabled.
            except(TypeError, ZeroDivisionError):
                messages.error(request, 'ERROR!You didnt chose the Table.Choose Table first')
            if len(lst_h) > 0:
                if len(old_data) > 0:
                    logging.debug('table was with data')
                    try:
                        a = tbl
                        increment = int(len(tbl) / len(lst_h))
                        b = np.array(a).reshape(increment, len(lst_h))
                        logging.debug(b)
                        logging.debug(set(tbl))
                        c = tuple(b)
                        print(c)
                        d = [i[0] for i in b]
                        logging.debug(set([x for x in d if e.count(x) > 1]))
                        g = set([x for x in d if e.count(x) > 1])
                    except(ZeroDivisionError):
                        messages.error(request, 'DivisionByZero Error')
                    except(TypeError):
                        messages.error(request, 'Chose Table first')
                    cursor = connection.cursor()
                    # ------------------------------------------------------------------------------------------------------------------------
                    logging.debug('-----------')
                    logging.debug(d)
                    logging.debug(set(d))
                    if tbl[0] in g:
                        messages.error(request, 'Code KEY dublicate Error! Code field cant have a dublicates')

                    if len(d) != len(set(d)):  # check if dublicates in new input data
                        messages.error(request, 'Code KEY dublicate Error! Code field cant have a dublicates')

                    else:
                        # check if in new input containe dublicates
                        for i in range(len(c)):
                            for j in range(len(c[0])):
                                if d_t[j] == 'num':
                                   if not str(c[i][j]).isnumeric():
                                       messages.error(request, 'Error!Integer data type must have numeric value!')
                                if len(c[i][j]) > int(length[j]):
                                    messages.error(request, 'Error!Length of input value is to big!')
                        try:
                            with connection.cursor() as cursor:  # add new column to db table
                                cursor.execute(
                                    '''TRUNCATE TABLE engine_app_''' + dim.lower() + ''' RESTART IDENTITY;''')
                                logging.debug('delete all items')
                            insert_in_db(lst_h, c, dim.lower())
                            messages.success(request, 'Data was successfully saved')
                        except(DataError):
                            messages.error(request, 'Wrong data type in input.Insert data in right fotmat')
                        except(UnboundLocalError):
                            messages.error(request, 'Chose Table first')
                else:
                    logging.debug('table was empty')
                    try:
                        increment = int(len(tbl) / len(lst_h))  #
                        a = tbl
                        b = np.array(a).reshape(increment, len(lst_h))
                        logging.debug(b)
                        c = tuple(b)
                        d = [i[0] for i in b]  # list of inputs with first index only
                        logging.debug(d)
                        logging.debug(set([x for x in d if d.count(x) > 1]))  # set of list d to check for dublicates
                    except(ZeroDivisionError):
                        messages.error(request, 'DivisionByZero Error')
                    # except(TypeError ):
                    # messages.error(request, 'Chose Table first')
                    cursor = connection.cursor()
                    if len(tbl) > 0 and '' not in d:
                        logging.debug('tbl is not empty')
                        logging.debug(d)
                        logging.debug(set(d))
                        if len(d) != len(set(d)):
                            messages.error(request, 'Code KEY dublicate Error! Code field cant have a dublicates')
                            logging.debug('tbl in d ' + str(tbl[i]))
                        else:
                            logging.debug('no dublicates detected')
                            for i in range(len(c)):
                                for j in range(len(c[0])):
                                    if d_t[j] == 'num':
                                        if not str(c[i][j]).isnumeric():
                                            messages.error(request, 'Error!Integer data type must have numeric value!')
                                    if len(c[i][j]) > int(length[j]):
                                        messages.error(request, 'Error!Length of input value is to big!')
                            try:
                                with connection.cursor() as cursor:  # add new column to db table
                                    cursor.execute(
                                        '''TRUNCATE TABLE engine_app_''' + dim.lower() + ''' RESTART IDENTITY;''')
                                    logging.debug('delete all items')
                                insert_in_db(lst_h, c, dim.lower())
                                messages.success(request, 'Data was successfully saved')
                            except(DataError):
                                messages.error(request, 'Wrong data type in input.Insert data in right fotmat')
                            except(UnboundLocalError):
                                messages.error(request, 'Chose Table first')
                    else:
                        messages.warning(request, 'No changes detected')

        if 'export' in request.POST:
            logging.debug('export_mapping_t')
            option = request.POST.get('dim')  # get the selected option and set it as table name
            new_name = request.POST.get('new_name_mt')
            logging.debug(new_name)
            #breakpoint()
            var_db = conver_right_formt_of_tbl_name(option)
            var_db_1 = conver_right_formt_of_tbl_name(new_name)
            logging.debug(var_db_1)
            cursor = connection.cursor()
            # SQL code to return columns from table
            sql_string = '''select * from engine_app_''' + var_db.lower()
            print(sql_string)
            sql_string_header = '''select column_name from information_schema.columns where table_name='engine_app_''' + var_db.lower() + '''' '''
            cursor.execute(sql_string)
            sql_columns = cursor.fetchall()
            cursor.execute(sql_string_header)
            sql_header = cursor.fetchall()
            logging.debug(sql_columns)
            logging.debug(sql_header)
            list_np_export = np.array(sql_columns)
            list_np_export_h = np.array([str(x) for x, in sql_header])
            logging.debug('im here')
            logging.debug(list_np_export_h[1:])
            logging.debug(list_np_export[1:])
            if len(list_np_export) > 0:
                list_np_ex = np.vstack((list_np_export_h, list_np_export))
                logging.debug(list_np_ex)
                #converting numpy array into data frame to export as xlsx file
                df = pd.DataFrame(data=list_np_ex[1:, 1:],  # values
                index = list_np_ex[1:, 0],  # 1st column as index
                columns = list_np_ex[0, 1:])  # 1st row as the column names
            else:
                list_empty = []
                for i in range(len(list_np_export_h)):
                    list_empty.append('')
                logging.debug('-----ddd----------')
                logging.debug(list_empty)
                list_np_ex = np.vstack((list_np_export_h, list_empty))
                logging.debug(list_np_ex)
                # converting numpy array into data frame to export as xlsx file
                df = pd.DataFrame(data=list_np_ex[1:, 1:],  # values
                                  index=list_np_ex[1:, 0],  # 1st column as index
                                  columns=list_np_ex[0, 1:])  # 1st row as the column names


            logging.debug(df)
            try:
                os.mkdir(path)
            except OSError:
                logging.debug("Creation of the directory %s failed" % path)
            else:
                logging.debug("Successfully created the directory %s " % path)

            df.to_excel(r'C:\Users\\'+username+'\Desktop\Engine\\' + var_db_1.lower() + '_' + now.strftime(
                "%Y%m%d_%H%M%S") + '.xlsx', index=False)
            var_db = ''
            option = ''
            messages.success(request, "Data was exported to your Desktop.")
    context = {
        'obj_dim_name': obj_dim_name,
        'list_np': list_np,
        'var_template': var_template,
        'list_header': list_var,
        'option': var_db,
        'title':option,
        'list_np_dt':list_np_dt
    }
    return render(request, 'brows _mapping_t.html', context)

@login_required(login_url='user_login')
def brows_define_mrules(request): #shows the mapping rule/ define mapping rulles/ mapping key kan be 0<=3
    obj_1 = Mapping_Data.objects.all()
    obj = Dimensions.objects.all()
    rule_main = Mapping_Rules_Main.objects.all().order_by('id')
    option_m = ''
    option_d_h = ''
    option_m_f = ''
    option = ''
    mapping_select = ''
    dimension_select = ''
    sql_string_header_2 = ''
    list_var = []
    list_var_2 = []
    list_var_3 = []
    list_var_5 = []
    tempo_in = []
    tempo_out = []
    var_template = ''
    rule_name = ''
    bool_in = False
    bool_out = False
    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')

        if request.POST.get('action') == 'select':
            logging.debug('select')
            option = request.POST.get('dimName')  # get the selected option and set it as table name
            a = mapping_rules_select(option, dimension_select, list_var)
            data = {'var_template': a["var_template"],
                    'list_var': a["list_var"]}
            return JsonResponse(data)

        if request.POST.get('action') == 'select_1':
           option = request.POST.get('dimName_f')  # get the selected option and set it as table name
           data = {'field': option,}
           return JsonResponse(data)

        if request.POST.get('action') == 'select_2':
            logging.debug('select_2')
            option_m = request.POST.get('mtName')  # get the selected option and set it as table name
            logging.debug(option_m)
            obj_mt = Mapping_Data.objects.get(name=option_m)
            logging.debug(obj_mt.new_name)
            a = mapping_rule_select_mt(option_m, mapping_select, dimension_select, list_var_2)
            data = {'mapping_t': a["mapping_t"],
                    'list_var_2': a["list_var_2"],
                    'new_nm': obj_mt.new_name, }
            return JsonResponse(data)

        if request.POST.get('action') == 'select_3':
           option = request.POST.get('mtName_f')  # get the selected option and set it as table name
           data = {'field': option,}
           return JsonResponse(data)

        if request.POST.get('action') == 'select_6':
           logging.debug('select_6')
           option = request.POST.get('output_f')  # get the selected option and set it as table name
           data = {'output_f': option,}
           return JsonResponse(data)

        if request.POST.get('action') == 'select_7':
           logging.debug('select_7')
           option = request.POST.get('target_d')  # get the selected option and set it as table name
           data = {'target_d': option,}
           return JsonResponse(data)


        if request.POST.get('action') == 'select_s':
            logging.debug('select_s')
            option = request.POST.get('dimName')  # get the selected option and set it as table name
            a = mapping_rules_select(option, dimension_select, list_var)
            data = {'var_template': a["var_template"],
                    'list_var': a["list_var"]}
            return JsonResponse(data)

        if request.POST.get('action') == 'select_1_s':
           option = request.POST.get('dimName_f')  # get the selected option and set it as table name
           data = {'field': option,}
           return JsonResponse(data)

        if request.POST.get('action') == 'select_2_s':
            logging.debug('select_2_s')
            option_m = request.POST.get('mtName') # get the selected option and set it as table name
            logging.debug(option_m)
            a = mapping_rule_select_mt(option_m, mapping_select, dimension_select, list_var_2)
            data = {'mapping_t': a["mapping_t"],
                    'list_var_2': a["list_var_2"]}
            return JsonResponse(data)

        if request.POST.get('action') == 'select_3_s':
           option = request.POST.get('mtName_f')  # get the selected option and set it as table name
           data = {'field': option,}
           return JsonResponse(data)

        if request.POST.get('action') == 'select_6_s':
           logging.debug('select_6_s')
           option = request.POST.get('output_f')  # get the selected option and set it as table name
           data = {'output_f': option,}
           return JsonResponse(data)

        if request.POST.get('action') == 'select_7_s':
           logging.debug('select_7_s')
           option = request.POST.get('target_d')  # get the selected option and set it as table name
           data = {'target_d': option}
           return JsonResponse(data)

        if request.POST.get('action') == 'select_t':
            logging.debug('select_t')
            option = request.POST.get('dimName')  # get the selected option and set it as table name
            a = mapping_rules_select(option, dimension_select, list_var)
            data = {'var_template': a["var_template"],
                    'list_var': a["list_var"]}
            return JsonResponse(data)

        if request.POST.get('action') == 'select_1_t':
           option = request.POST.get('dimName_f')  # get the selected option and set it as table name
           data = {'field': option,}
           return JsonResponse(data)

        if request.POST.get('action') == 'select_2_t':
            logging.debug('select_2_t')
            option_m = request.POST.get('mtName') # get the selected option and set it as table name
            a = mapping_rule_select_mt(option_m, mapping_select, dimension_select, list_var_2)
            data = {'mapping_t': a["mapping_t"],
                    'list_var_2': a["list_var_2"]}
            return JsonResponse(data)

        if request.POST.get('action') == 'select_3_t':
           option = request.POST.get('mtName_f')  # get the selected option and set it as table name
           data = {'field': option,}
           return JsonResponse(data)

        if request.POST.get('action') == 'select_6_t':
           logging.debug('select_6')
           option = request.POST.get('output_f')  # get the selected option and set it as table name
           data = {'output_f': option,}
           return JsonResponse(data)

        if request.POST.get('action') == 'select_7_t':
           logging.debug('select_7_t')
           option = request.POST.get('target_d')  # get the selected option and set it as table name
           data = {'target_d': option,}
           return JsonResponse(data)

        if 'save' in request.POST:# getting all defined mapping keys and save as rule in db

            logging.debug('save')
            dName = request.POST.get('Dname')
            input_dim = request.POST.get('input_dim')
            input_dim_f = request.POST.get('input_dim_f')
            input_mt = request.POST.get('input_mt')
            input_mt_f = request.POST.get('input_mt_f')
            input_dim_s = request.POST.get('input_dim_s')
            input_dim_f_s = request.POST.get('input_dim_f_s')
            input_mt_f_s = request.POST.get('input_mt_f_s')
            input_dim_t = request.POST.get('input_dim_t')
            input_dim_f_t = request.POST.get('input_dim_f_t')
            input_mt_f_t = request.POST.get('input_mt_f_t')

            output_f = request.POST.get('output_f')
            target_d = request.POST.get('target_d')
            output_f_s = request.POST.get('output_f_s')
            target_d_s = request.POST.get('target_d_s')
            output_f_t = request.POST.get('output_f_t')
            target_d_t = request.POST.get('target_d_t')

            input_p = request.POST.getlist('inputP')
            output_p = request.POST.getlist('outputP')
            row_inpt = request.POST.getlist('rowInpt')
            row_otpt = request.POST.getlist('rowOtpt')

            if len(input_p) == 1:
                input_p = [input_p[0],'','']
            if len(output_p) == 1:
                output_p = [output_p[0],'','']
            if len(row_inpt) == 1:
                row_inpt = [row_inpt[0],'','']
            if len(row_otpt) == 1:
                row_otpt = [row_otpt[0],'','']
            logging.debug(input_p)
            logging.debug(output_p)
            logging.debug(row_inpt)
            logging.debug(row_otpt)
            logging.debug('-----inputs------')
            logging.debug(dName)
            logging.debug(input_dim)
            logging.debug(input_dim_f)
            logging.debug(input_mt)
            logging.debug(input_mt_f)
            logging.debug(input_dim_s)
            logging.debug(input_dim_f_s)
            logging.debug(input_mt_f_s)
            logging.debug(input_dim_t)
            logging.debug(input_dim_f_t)
            logging.debug(input_mt_f_t)
            logging.debug('-----outputs------')
            logging.debug(output_f)
            logging.debug(target_d)
            logging.debug(output_f_s)
            logging.debug(target_d_s)
            logging.debug(output_f_t)
            logging.debug(target_d_t)
            logging.debug(max(row_inpt))
            logging.debug(max(row_otpt))
            #check if all rows all filled.--------------------------------------------------------
            if int(max(row_inpt)) == 1:
                logging.debug('len 1')
                if input_dim != None and input_dim_f != None and input_mt != None and input_mt_f != None:
                    bool_in = True
            if int(max(row_inpt)) == 2:
                logging.debug('len 2')
                if input_dim != None and input_dim_f != None and input_mt != None and input_mt_f != None\
                        and input_dim_s != None and input_dim_f_s != None and input_mt_f_s != None:
                    bool_in = True
            if int(max(row_inpt)) == 3:
                logging.debug('len 3')
                if input_dim != None and input_dim_f != None and input_mt != None and input_mt_f != None\
                        and input_dim_s != None and input_dim_f_s != None and input_mt_f_s != None\
                            and input_dim_t != None and input_dim_f_t != None and input_mt_f_t != None:
                    bool_in = True

            if int(max(row_otpt)) == 1:
                logging.debug('len 1 out')
                if output_f != None and target_d != None:
                    bool_out = True
            if int(max(row_otpt)) == 2:
                logging.debug('len 2 out')
                if output_f != None and target_d != None and output_f_s != None and target_d_s != None:
                    bool_out = True
            if int(max(row_otpt)) == 3:
                logging.debug('len 3 out')
                if output_f != None and target_d != None and output_f_s != None and target_d_s != None and output_f_t != None and target_d_t != None:
                    bool_out = True
            logging.debug(bool_in)
            logging.debug(bool_out)
            #breakpoint()
            if bool_in is True and bool_out is True:
                logging.debug('bool is true')
                #breakpoint()
                list_inputs_1 = [dName, input_dim, input_dim_f, input_mt, input_mt_f,str(row_inpt[0]),input_p[0]]
                list_inputs_2 = [dName, input_dim_s, input_dim_f_s, input_mt, input_mt_f_s, str(row_inpt[1]), input_p[1]]
                list_inputs_3 = [dName, input_dim_t, input_dim_f_t, input_mt, input_mt_f_t, str(row_inpt[2]), input_p[2]]
                lists_in_one = [list_inputs_1,list_inputs_2,list_inputs_3]
                new_inputs_list = np.array(list_inputs_1)
                count = 1
                for i in range(1,len(input_p)):
                    if input_p[i] != '':
                        new_inputs_list = np.append(new_inputs_list,lists_in_one[i])
                        count += 1
                logging.debug(new_inputs_list)
                a = np.reshape(new_inputs_list,(count,-1))
                logging.debug(a)
                list_outputs_1 = [dName, target_d , None, input_mt, output_f,str(row_otpt[0]),output_p[0]]
                list_outputs_2 = [dName, target_d_s, None, input_mt, output_f, str(row_otpt[1]), output_p[1]]
                list_outputs_3 = [dName, target_d_t, None, input_mt, output_f, str(row_otpt[2]), output_p[2]]
                lists_in_one_2 = [list_outputs_1, list_outputs_2, list_outputs_3]
                test = str(row_otpt[0])
                logging.debug(type(test))
                new_outpts_list = np.array(list_outputs_1)
                count = 1
                for i in range(1, len(output_p)):
                    if output_p[i] != '':
                        new_outpts_list = np.append(new_outpts_list, lists_in_one_2[i])
                        count += 1
                logging.debug(count)
                b = np.reshape(new_outpts_list, (count, -1))
                logging.debug(b)
                logging.debug('-----------------')
                logging.debug(np.concatenate((a,b), axis=0))
                c = np.concatenate((a,b), axis=0)
                df = pd.DataFrame(data=c)
                logging.debug(df)
                list_of_rules = Mapping_Rules_Main.objects.all().values_list('ruleName')
                logging.debug(list_of_rules)

                if dName != 'New Rule' and dName not in list_of_rules:
                    #breakpoint()

                    if dName is not None and input_dim is not None and input_dim_f is not None and\
                            input_mt is not None and input_mt_f is not None and  output_f is not None and target_d:
                        rules_obj = Mapping_Rules_Main.objects.create(
                            ruleName=dName
                        )
                        rules_obj.save()
                        try:
                            for i in range(len(c)):
                                    rule_obj_1 = ''
                                    field = np.str(c[i][3])
                                    logging.debug(type(field))
                                    logging.debug(field)
                                    rule_obj_1 = Mapping_Rules.objects.create(
                                        ruleName=Mapping_Rules_Main.objects.get(ruleName=c[i][0]),
                                        dimensionName=Dimensions.objects.get(dimensionName=c[i][1]),
                                        dimField=c[i][2],
                                        mtName=Mapping_Data.objects.get(name=field),
                                        mtField=c[i][4],
                                        row=c[i][5],
                                        type=c[i][6],
                                    )
                            rule_obj_1.save()
                        except Exception :
                                messages.error(request,"Error! The rule with name \""+dName+"\" allready exist.")
                else:
                    messages.success(request, 'Error!Default Rule name must be changed.')
            else:
                messages.success(request, 'Error!!!All active fields must be selected.')
        if 'delete' in request.POST:
            dName = request.POST.get('Dname')
            dName_old = request.POST.get('rule_name')
            logging.debug(dName_old)

            if dName is not None:
                rule_obj_1 = Mapping_Rules_Main.objects.get(
                    ruleName=dName
                )
                logging.debug(rule_obj_1.id)
                rule_obj = Mapping_Rules.objects.filter(
                    ruleName = rule_obj_1.id
                ).delete()
                rule_obj_1 = Mapping_Rules_Main.objects.get(
                    ruleName=dName
                ).delete()
                messages.success(request, 'Rule -' + str(dName) + '- was deleted.')
            else:
                rule_obj_1 = Mapping_Rules_Main.objects.get(
                    ruleName=dName_old
                )
                logging.debug(rule_obj_1.id)
                rule_obj = Mapping_Rules.objects.filter(
                    ruleName=rule_obj_1.id
                ).delete()
                rule_obj_1 = Mapping_Rules_Main.objects.get(
                    ruleName=dName_old
                ).delete()
                messages.success(request, 'Rule -' + str(dName) + '- was deleted.')
        if 'apply' in request.POST: #change the mapping rule (need to handle the exceptions!!!!!!!!!!update 23.12)
             logging.debug('update')
             dName = request.POST.get('Dname')
             input_dim = request.POST.get('input_dim')
             input_dim_f = request.POST.get('input_dim_f')
             input_mt = request.POST.get('input_mt')
             input_mt_f = request.POST.get('input_mt_f')
             input_dim_s = request.POST.get('input_dim_s')
             input_dim_f_s = request.POST.get('input_dim_f_s')
             input_mt_f_s = request.POST.get('input_mt_f_s')
             input_dim_t = request.POST.get('input_dim_t')
             input_dim_f_t = request.POST.get('input_dim_f_t')
             input_mt_f_t = request.POST.get('input_mt_f_t')
             output_f = request.POST.get('output_f')
             target_d = request.POST.get('target_d')
             output_f_s = request.POST.get('output_f_s')
             target_d_s = request.POST.get('target_d_s')
             output_f_t = request.POST.get('output_f_t')
             target_d_t = request.POST.get('target_d_t')

             input_p = request.POST.getlist('inputP')
             output_p = request.POST.getlist('outputP')
             row_inpt = request.POST.getlist('rowInpt')
             row_otpt = request.POST.getlist('rowOtpt')
             list_inputs = request.POST.getlist('list_inputs')
             list_outpts = request.POST.getlist('list_outpts')

             inputs_clicked = request.POST.get('inputs_clicked')
             outputs_clicked = request.POST.get('outputs_clicked')

             list_row_in = request.POST.getlist('list_row_in')
             list_row_out = request.POST.getlist('list_row_out')
             logging.debug(list_inputs)
             logging.debug(list_outpts)
             logging.debug(inputs_clicked)
             logging.debug(outputs_clicked)
             logging.debug(list_row_in)
             logging.debug(list_row_out)
             logging.debug('----------')
             if inputs_clicked is None:
                 input_p = list_inputs
                 row_inpt = list_row_in
             if outputs_clicked is None:
                 output_p = list_outpts
                 row_otpt = list_row_out
             for i in range(len(input_p),3):
                 input_p.append('')
                 row_inpt.append('')
             for i in range(len(output_p),3):
                 output_p.append('')
                 row_otpt.append('')
             logging.debug(input_p)
             logging.debug(output_p)
             logging.debug(row_inpt)
             logging.debug(row_otpt)
             logging.debug('-----inputs------')
             logging.debug(dName)
             logging.debug(input_dim)
             logging.debug(input_dim_f)
             logging.debug(input_mt)
             logging.debug(input_mt_f)
             logging.debug(input_dim_s)
             logging.debug(input_dim_f_s)
             logging.debug(input_mt_f_s)
             logging.debug(input_dim_t)
             logging.debug(input_dim_f_t)
             logging.debug(input_mt_f_t)
             logging.debug('-----outputs------')
             logging.debug(output_f)
             logging.debug(target_d)
             logging.debug(output_f_s)
             logging.debug(target_d_s)
             logging.debug(output_f_t)
             logging.debug(target_d_t)
             rule = Mapping_Rules_Main.objects.values_list('ruleName', flat=True)
             logging.debug(rule)
             logging.debug(np.array(input_p))
             logging.debug(np.array(output_p))
             new_list = input_p + output_p
             list_inputs_1 = [dName, input_dim, input_dim_f, input_mt, input_mt_f, str(row_inpt[0]), input_p[0]]
             list_inputs_2 = [dName, input_dim_s, input_dim_f_s, input_mt, input_mt_f_s, str(row_inpt[1]), input_p[1]]
             list_inputs_3 = [dName, input_dim_t, input_dim_f_t, input_mt, input_mt_f_t, str(row_inpt[2]), input_p[2]]
             lists_in_one = [list_inputs_1, list_inputs_2, list_inputs_3]
             new_inputs_list = np.array(list_inputs_1)
             count = 1
             for i in range(1, len(input_p)):
                 if input_p[i] != '':
                     new_inputs_list = np.append(new_inputs_list, lists_in_one[i])
                     count += 1
             logging.debug(new_inputs_list)
             a = np.reshape(new_inputs_list, (count, -1))
             logging.debug(a)
             list_outputs_1 = [dName, target_d, None, input_mt, output_f, str(row_otpt[0]), output_p[0]]
             list_outputs_2 = [dName, target_d_s, None, input_mt, output_f_s, str(row_otpt[1]), output_p[1]]
             list_outputs_3 = [dName, target_d_t, None, input_mt, output_f_t, str(row_otpt[2]), output_p[2]]
             lists_in_one_2 = [list_outputs_1, list_outputs_2, list_outputs_3]
             test = str(row_otpt[0])
             logging.debug(type(test))
             new_outpts_list = np.array(list_outputs_1)
             count = 1
             for i in range(1, len(output_p)):
                 if output_p[i] != '':
                     new_outpts_list = np.append(new_outpts_list, lists_in_one_2[i])
                     count += 1
             logging.debug(count)
             b = np.reshape(new_outpts_list, (count, -1))
             logging.debug(b)
             logging.debug('----------YYYYYYYYYY-------')
             logging.debug(np.concatenate((a, b), axis=0))
             c = np.concatenate((a, b), axis=0)

             rules_obj = Mapping_Rules_Main.objects.get(
                 ruleName=dName
             )
             rules_obj.save()
             for i in range(len(c)):
                 rule_obj_1 = ''
                 field = np.str(c[i][3])
                 logging.debug(type(field))
                 logging.debug(field)
                 logging.debug('hhh------------hhh')
                 logging.debug(c[i][6])
                 try:
                     a = Mapping_Rules.objects.get(ruleName=Mapping_Rules_Main.objects.get(ruleName=c[i][0]),
                         row = c[i][5],
                          type= c[i][6])

                     logging.debug(a)
                     if c[i][1] is not None:
                        a.dimensionName = Dimensions.objects.get(dimensionName=c[i][1])
                     if c[i][2] is not None:
                        a.dimField = c[i][2]
                     if c[i][3] is not None:
                        a.mtName = Mapping_Data.objects.get(name=c[i][3])
                     if c[i][4] is not None:
                        a.mtField = c[i][4]
                     a.save()
                 except(Exception ):
                     a = Mapping_Rules.objects.get(ruleName=Mapping_Rules_Main.objects.get(ruleName=c[i-1][0]),
                                                   row=c[i-1][5],
                                                   type=c[i-1][6])

                     b = Mapping_Rules.objects.create(ruleName=Mapping_Rules_Main.objects.get(ruleName=c[i][0]),
                                                   dimensionName = Dimensions.objects.get(dimensionName=c[i][1]),
                                                   dimField = c[i][2],
                                                   mtName = a.mtName,
                                                   mtField = c[i][4],
                                                   row=c[i][5],
                                                   type=c[i][6],
                                                      )

                     logging.debug(a)

                     a.save()



        if 'rule_submit' in request.POST or 'add_rule' in request.POST:
            logging.debug('rule_name')
            rule_name = request.POST.get('rule_submit')
            if rule_name is not None:
                logging.debug(rule_name)
                rules_n = Mapping_Rules_Main.objects.get(ruleName=str(rule_name))
                rules_obj = Mapping_Rules.objects.filter(ruleName=rules_n).order_by('id')
                logging.debug('----')
                list_inputs = []
                logging.debug(list_inputs)
                cursor = connection.cursor()
                for i in range(len(rules_obj)):
                    test = rules_obj[i]
                    if (rules_obj[i].type == 'input'):
                        tempo_in.append(test)
                    if (rules_obj[i].type == 'output'):
                        tempo_out.append(test)

                    var_dimension = str(rules_obj[i].dimensionName.dimensionName).replace(' ', '_')
                    var_mapping_t = str(rules_obj[i].mtName.name).replace(' ', '_')
                    logging.debug(var_dimension)
                    # SQL code to return columns from table
                    sql_string_header = '''select column_name from information_schema.columns where table_name='engine_app_''' + var_dimension.lower() + '''' '''
                    sql_string_header_2 = '''select column_name from information_schema.columns where table_name='engine_app_''' + var_mapping_t.lower() + '''' '''
                    cursor.execute(sql_string_header)
                    sql_columns_header = cursor.fetchall()
                    list_header = np.array(sql_columns_header)
                    logging.debug('-------------')
                    logging.debug(list_header)
                for i in range(list_header.__len__()):
                    logging.debug(list_header.item(i))
                    if (list_header.item(i) != 'id'):
                        list_var.append(list_header.item(i))
                logging.debug(tempo_in)
                logging.debug(tempo_out)
                #logging.debug(tempo_out[1].mtField)
                logging.debug('----------1')
                logging.debug(list_var)
                list_var_5 =  exequte_sql(sql_string_header_2,list_var_2)

            else:
                list_var = [' ']
                list_var_5 = [' ']
                tempo_in =['input']
                tempo_out = ['output']
                rule_name = 'New Rule'

    context = {#send data to template
        'obj': obj,
        'obj_1': obj_1,
        'var_template':var_template,
        'list_var': list_var,
        'list_var_2': list_var_5,
        'list_var_3': list_var_3,
        'var_mepping_t':option_m,
        'dimension_select':dimension_select,
        'mapping_select':mapping_select,
        'option_d_h':option_d_h,
        'option_m_f':str(option_m_f),
        'option': option,
        'rules': rule_main,
        'rule_name':rule_name,
        'rules_obj':tempo_in,
        'rules_obj_out': tempo_out
    }
    return render(request, 'brows_define_mrules.html', context )

@login_required(login_url='user_login')
def brows_define_msets(request):# set mapping rules as set
    sets = Mapping_Sets.objects.all().order_by('id')
    sets_obj = ''
    list_final = ''
    reslt_list = ''
    if_new_set = ''
    list_update = []
    list_unactive_rls = []
    rules = Mapping_Rules_Main.objects.all().order_by('id')
    rule_tbl = Mapping_Rules.objects.all().order_by('id')
    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')

        if 'save' in request.POST:
            option = request.POST.getlist('select')
            set_name = request.POST.get('Dname')
            logging.debug(option)
            logging.debug(set_name)
            if set_name != 'New rule Set':
                for i in option:
                    logging.debug(i)
                    a = Mapping_Rules_Main.objects.get(ruleName = i)
                    logging.debug(a.id)
                    b = Mapping_Rules.objects.filter(ruleName = a.id)
                    logging.debug(b)
                    c = Mapping_Sets.objects.get_or_create(setName=set_name)
                    for i in range(len(b)):
                        logging.debug(b[i])
                        logging.debug(c)
                        #b[i].setName = Mapping_Sets.objects.get(setName=set_name)
                        b[i].save()
                        b[i].setName.add(Mapping_Sets.objects.get(setName=set_name))
            else:
                messages.error(request,"Error!Change default set name.")

        if 'add_set' in request.POST:
            logging.debug('add set')
            sets_obj = 'New rule Set'
            if_new_set = 'New'
            for i in rule_tbl:
                logging.debug(i.setName)
                if i.setName is not None:
                    list_unactive_rls.append(i.ruleName.id)
            reslt_list = list(dict.fromkeys(list_unactive_rls))
            logging.debug(reslt_list)
            for i in rules:
                if i.id not in reslt_list:
                    logging.debug(i.id)
                    list_update.append(i.ruleName)
            logging.debug(list_update)

        if 'set_submit' in request.POST:
            set_name = request.POST.get('set_submit')
            obj = Mapping_Sets.objects.get(setName=set_name)
            obj_1 = Mapping_Rules.objects.filter(setName=obj.id)
            logging.debug(obj_1)
            mylist = []
            for i in obj_1:
                logging.debug(i.ruleName.id)
                obj_2 = Mapping_Rules_Main.objects.get(id=i.ruleName.id)
                logging.debug(obj_2)
                mylist.append(obj_2.ruleName)
            logging.debug(list(dict.fromkeys(mylist)))
            list_final = list(dict.fromkeys(mylist))
            if set_name is not None:
                logging.debug(set_name)
                sets_obj = Mapping_Sets.objects.get(setName=set_name)
                sets_obj = sets_obj.setName

        if 'delete' in request.POST:
            set_name = request.POST.get('set_obj')
            logging.debug(set_name)
            obj = Mapping_Sets.objects.get(setName=set_name)
            obj_1 = Mapping_Rules.objects.filter(setName=obj.id)
            obj_2 = Mapping_Sets.objects.get(setName=set_name).delete()


    context = {
        'sets':sets,
        'rules':rules,
        'set_obj':sets_obj,
        'list_final':list_final,
        'rule_tbl':rule_tbl,
        'reslt_list':list_update,
        'if_new_set':if_new_set
    }
    return render(request, 'brows_define_msets.html', context)

@login_required(login_url='user_login')
def define_mapping_table(request):
    if 'logout_btn' in request.POST:
        logout(request)
        logging.debug('user loged out')
        return redirect('user_login')
    return render(request, 'define_mappingt.html')

@login_required(login_url='user_login')
def export_data(request):
    list_models = []
    result = []
    new_list_head = []
    model = ''
    fields = ''
    c = ''
    select = ''
    bool_exist = True
    obj_dim = Dimensions.objects.all()
    obj_mt =  Mapping_Data.objects.all()
    a = apps.all_models['engine_app'].values()
    logging.debug(a)
    for k in a:
        logging.debug(k.__name__)
        k = str(k.__name__).replace('_',' ')
        if k not in list_tbl_not_to_export:
            a = [k, 'none']
            if k in list_custom_dim:
                logging.debug('custom')
                x = Dimensions.objects.get(dimensionName=str(k).replace('_',' '))
                if x.new_name != None:
                    k = x.new_name
                    logging.debug(k)
                    a = [k, 'c']
                else:
                    a = ['','c']
            if k in list_mapping_t:
                logging.debug('mapping')
                y = Mapping_Data.objects.get(name=str(k).replace('_', ' '))
                if y.new_name != None:
                    k = y.new_name
                    a = [k, 'm']
                else:
                    a = ['','m']

            list_models.append(a)
    for i in list_models:
        logging.debug(str(i[0]))
        logging.debug(type(i[0]))
        if str(i[0]) != '':
            result.append(i)

    logging.debug(list_models)
    logging.debug(result)

    if 'logout_btn' in request.POST:
        logout(request)
        logging.debug('user loged out')
        return redirect('user_login')

    if 'select' in request.POST:
        select = request.POST.get('select')
        logging.debug(select)
        str_select = str(select).replace(' ','_')
        if select != '':
            try:
                dim_name = Dimensions.objects.get(new_name=str(select).replace('_',' '))
                logging.debug(dim_name)
                str_select =  str(dim_name.dimensionName).replace(' ','_')
                bool_exist = False
            except(Exception, LookupError):
                logging.debug('not exist dim')
                #Model = apps.get_model('engine_app', str_select)
            if bool_exist == True:
                try:
                    mt_name = Mapping_Data.objects.get(new_name=str(select).replace('_', ' '))
                    str_select = str(mt_name.name).replace(' ','_')
                except(LookupError,Exception):
                    logging.debug('not exist mt')
            Model = apps.get_model('engine_app', str_select)
            model = Model.objects.all().values_list()
            logging.debug(model)
            fields = [field.name for field in Model._meta.get_fields()]
            logging.debug(fields)
            list_new_custom = []
            for i in fields:
                logging.debug(i)
                if i in list_custom_dim_export:
                    logging.debug('in list')
                    item = Dimensions.objects.get(dimensionName=str(i).replace('_',' ').capitalize())
                    list_new_custom.append(str(item.new_name).replace(' ','_').lower())
                else:
                    logging.debug('not in list')
                    list_new_custom.append('')
            logging.debug(list_new_custom)
            new_list_head = zip(fields[1:],list_new_custom[1:])
            logging.debug(new_list_head)
            #breakpoint()
            b = pd.DataFrame(model)
            logging.debug(b)
            b = np.array(b)
            c = b[0:100,1:]
            logging.debug(b)
        else:
            messages.warning(request,'No table was chosen')


    if 'export' in request.POST:
        logging.debug('export')
        check =request.POST.getlist('check')
        db_tbl = request.POST.get('db_tbl')
        logging.debug(check)
        logging.debug(db_tbl)
        str_db_tbl = str(db_tbl).replace(' ', '_')
        if db_tbl == '' or db_tbl is None:
            messages.error(request,"Error! Choose a table first.")

        else:
            try:
                dim_name = Dimensions.objects.get(new_name=str(db_tbl).replace('_',' '))
                logging.debug(dim_name)
                str_db_tbl =  str(dim_name.dimensionName).replace(' ','_')

                bool_exist = False
            except(Exception, LookupError):
                logging.debug('not exist dim')
                #Model = apps.get_model('engine_app', str_select)
            if bool_exist == True:
                try:
                    mt_name = Mapping_Data.objects.get(new_name=str(db_tbl).replace('_', ' '))
                    logging.debug(mt_name)

                    str_db_tbl = str(mt_name.name).replace(' ','_')
                except(LookupError,Exception):
                    logging.debug('not exist mt')

            Model = apps.get_model('engine_app', str_db_tbl)
            model = Model.objects.all().values_list()
            fields_outpt = [field.name for field in Model._meta.get_fields()]
            logging.debug(model)
            b = pd.DataFrame(model)
            logging.debug(b)
            #b = np.array(b)
            g = []
            lst_fields = []
            logging.debug(g)
            for i in range(len(check)):
                lst_fields.append(fields_outpt[int(check[i])])
            logging.debug(lst_fields)
            list_customs = ['custom_1', 'custom_2', 'custom_3', 'custom_4']
            list_test = []
            for i in lst_fields:
                if i in list_customs:
                    logging.debug(i)
                    new_name_column = Dimensions.objects.get(dimensionName=str(i).replace('_',' ').capitalize()) ###update 14.12
                    new_name_column = new_name_column.new_name
                    logging.debug(new_name_column)
                    list_test.append(new_name_column.lower())
                else:
                    list_test.append(i.lower())
            logging.debug(list_test)
            lst_fields = list_test
            np.array(lst_fields)
            logging.debug(np.array(lst_fields))
            try:
                for i in range(len(check)):
                     logging.debug('loop')
                     e = np.array(b.iloc[:, int(check[i])])
                     g.append(e)

                logging.debug('----------')
                g = np.array(g)
                logging.debug(g)
                end_g = g.T
                logging.debug('----------111111111')
                logging.debug(end_g)
                end_arr = np.vstack([lst_fields, end_g])
                logging.debug(end_arr)
                logging.debug(end_arr[0])

                try:
                    df = pd.DataFrame(data=end_arr[1:, 0:],  # values
                                      index=end_arr[1:, 0],  # 1st column as index
                                      columns=end_arr[0, 0:])  # 1st row as the column names
                    logging.debug(df)
                    try:
                        os.mkdir(path)
                    except OSError:
                        logging.debug("Creation of the directory %s failed" % path)
                    else:
                        logging.debug("Successfully created the directory %s " % path)
                    df.to_excel(
                        r'C:\Users\\'+username+'\Desktop\Engine\\' + str(db_tbl).replace(' ','_').lower() + '_' + datetime.now().strftime(
                            "%Y%m%d_%H%M%S") + '.xlsx', index=False)
                    messages.success(request, "File was saved on your Desktop")
                except IndexError :
                    messages.error(request, "Error! At least one column must be checked.")
            except IndexError :
                messages.warning(request,'Empty table cant be exported.')

    context = {
        'list_models': result,
        'model': model,
        'obj_dim': obj_dim,
        'obj_mt': obj_mt,
        'fields': new_list_head,
        'b': c,
        'fileds_length':fields[1:],
        'select':select
    }
    return render(request, 'export_data.html', context)




@login_required(login_url='user_login')
def master_data(request):
#attributes
    dimension = ''
    dimension_name = ''
    column = ''
    column_1 =''
    dim_name = ''
    tbl = 'engine_app_'
    my_list = []
    list_np = []
    list_np_dt = []
    list_new_name = []
    list_new_name_t = []
    list_dimensions = ['Reporting Event', 'Reporting Period', 'Entity', 'Konto',
                        'Partner', 'Movement Type', 'Investe', 'Document Type']
    list_custom_dim = ['Custom 1', 'Custom 2', 'Custom 3', 'Custom 4']
#objects
    Dimensions.objects.all().order_by('id')
    data_type = Dimensions._meta.get_field('dimensionName').get_internal_type()
    obj = Dimensions.objects.all().order_by('id')
    obj_event = Reporting_Event.objects.all()

#########################################################################################################################
    if request.method == 'POST': #get list of dimension names
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')
        if 'dimension' in request.POST:
            dim_name = request.POST.get('dimension')
            print(dim_name)
            dim_name_check = dim_name
            dim_name_attr_old = dim_name
            #dimname equals input of dimension.so new_name must object od dimension
            if str(dim_name_check) not in list_dimensions and str(dim_name_check) not in list_custom_dim:
                logging.debug(1)
                p = Dimensions.objects.filter(new_name=str(dim_name)).values('id')  # change custom 1 to attribute!!!!
                a = str(p)
                print(a)
                key = int(''.join([i for i in a if i.isdigit()]))
                c = Dimensions.objects.get(id=key)
                g = c.dimensionName
                dimension_name = g#so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                dim_name = g
                print(str(dim_name)+ ' not in both lists')
            if str(dim_name_check) not in list_dimensions and str(dim_name_check) in list_custom_dim:
                logging.debug(2)
                #dim_name = g#so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                print(str(dim_name)+ ' in custom list')
                p = Dimensions.objects.filter(dimensionName=str(dim_name)).values('id')  # change custom 1 to attribute!!!!
                a = str(p)
                print(a)
                key = int(''.join([i for i in a if i.isdigit()]))
                c = Dimensions.objects.get(id=key)
                g = c.new_name
                dimension_name = g  # so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                print(g)
            #else:
            if dim_name:
                logging.debug(3)
                dimension = dim_name
                dim = dimension.replace(' ', '_')
                cursor = connection.cursor()
                # SQL code to return columns from table
                sql_string = '''SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name   = 'engine_app_'''+ dim.lower() + ''''; '''
                sql_data_type = '''SELECT column_name, character_maximum_length, numeric_precision
                                    FROM information_schema.columns
                                    WHERE table_schema = 'public'
                                    AND table_name   = 'engine_app_'''+dim.lower() +'\' and column_name <> \'id\';'''
                cursor.execute(sql_string)
                sql_columns = cursor.fetchall()
                cursor.execute(sql_data_type)
                sql_data_t = cursor.fetchall()
                logging.debug(sql_columns)
                logging.debug('öööööööööööööööööö')
                logging.debug(sql_data_t)
                list_np = np.array(sql_columns)
                list_np_dt = np.array(sql_data_t)
                logging.debug(list_np_dt)
                dimension_name = dim_name_attr_old#in the end we need to show the new name,so we sett to attribute dimension the name of POST request
#########################################################################################################################
                print(str(dimension_name)+' get_dim name' )
        if 'Dname' in request.POST:#change name of custom dimensions
            dim_name = request.POST.get('submit_fields')
            dim_name_attr_old = dim_name
            column_1 = request.POST.get('Dname')
            print(str(dim_name_attr_old) +' update dim name')
            print(column_1)
            if column_1  is not None:
                try:
                    print('try')
                    dim_tempo = column_1
                    dim_name_label = column_1.replace(' ', '_')
                    a = Dimensions.objects.values_list('new_name')

                    print(np.array(a))
                    list = np.array(a)
                    list_new_name_t = list
                    for i in range(list.__len__()):
                        if list.item(i) != None:
                            list_new_name.append(list.item(i))
                    print(list_new_name)
                    #with connection.cursor() as cursor:  # add new column to db table
                    print('try1')
                    eq = Dimensions.objects.filter(dimensionName=str(dim_tempo))
                    print(eq)
                    if str(dim_name_attr_old).lower() == str(column_1).lower() or str(dim_name_attr_old).lower() == 'None':
                        messages.success(request, 'Name of Dimension ' + dim_name_label.upper() + " hade no chenges")
                    else:
                        for i in range(list_custom_dim.__len__()): # compare custom dim and add new name of custom dim
                            if str(dim_name_attr_old) == list_custom_dim[i]:#check if dim name equals one of customs dim
                                p = Dimensions.objects.filter(dimensionName=str(list_custom_dim[i])).values('id')#change custom 1 to attribute!!!!
                                a = str(p)
                                key = int(''.join([i for i in a if i.isdigit()]))
                                Dimensions.objects.filter(id=key).update(new_name=str(column_1))
                            if i < list_new_name.__len__() and str(dim_name_attr_old) == list_new_name[i]:#if not then custom was changed and the dim name comes from column new_name and must be compared
                            #if str(dim_name_attr_old) in list_new_name and str(dim_name_attr_old) == list_new_name[i]:
                                p = Dimensions.objects.filter(dimensionName=str(list_custom_dim[i])).values('id')
                                a = str(p)
                                key = int(''.join([i for i in a if i.isdigit()]))
                                Dimensions.objects.filter(id=key).update(new_name=str(column_1))
                        messages.success(request, 'Name of Dimension ' + dim_name_label.upper() + " was changed")
                except (ProgrammingError):
                    messages.warning(request,'Error! somethin goes wrong with save changes')
#########################################################################################################################

        if 'submit_fields' in request.POST and 'submit_fields' is not None: #add columns to dimension and save changes
            column_2 = request.POST.get('submit_fields')
            column_3 = request.POST.get('Dname')
            list_columns = request.POST.getlist('list_np_dt')
            logging.debug(str(column_2)+' submit fields')
            logging.debug(str(column_3) + ' Dname')
            logging.debug(list_columns)
            #change the custom dimension to old name
            try:
                if str(column_2) not in list_dimensions and str(column_2) not in list_custom_dim:
                    p = Dimensions.objects.filter(new_name=str(column_3)).values('id')  # change custom 1 to attribute!!!!
                    print(p)
                    a = str(p)
                    print(a+' id')
                    key = int(''.join([i for i in a if i.isdigit()]))
                    c = Dimensions.objects.get(id=key)
                    g = c.dimensionName
                    dimension_name = g#so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                    column_2 = g
            except(TypeError,ValueError):
                messages.warning(request, "Error! change cant be done")

#change columns are allready exsists
            counter = 0
            while(counter < len(list_columns)):
                column_name = request.POST.get('Dname_' + str(counter+1))
                column_dt = request.POST.get('D_data_type_' + str(counter + 1))
                column_len = request.POST.get('D_length_' + str(counter + 1))
                logging.debug(column_name)
                logging.debug(column_dt)
                logging.debug(column_len)
                if counter == 0:
                    column_name = 'code'
                if counter == 1:
                    column_name = 'long_descr'
                if counter == 2:
                    column_name = 'short_descr'
                logging.debug(column_name)
                try:
                    dim_name = column_2.replace(' ', '_')
                    logging.debug('try')

                    if column_dt == 'character':
                        data_type = 'varchar'
                    if column_dt == 'integer':
                        data_type = 'numeric'
                    #future update add max len of attribute
                      # add new column to db table

                    logging.debug(column_name)
                    logging.debug(list_columns)
                    logging.debug(counter)
                    logging.debug(list_columns[counter])
                    logging.debug(data_type)
                    logging.debug('''ALTER TABLE engine_app_''' + dim_name.lower() + '''
                                            ALTER COLUMN ''' + column_name.lower() + ' TYPE ' + data_type +'(' + column_len + ',0) '
                                            'USING ' + column_name.lower() + ' :: ' + data_type +'; ''')
                    #breakpoint()
                    if column_name != list_columns[counter]:
                        with connection.cursor() as cursor:
                            cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + ''' 
                            RENAME COLUMN '''+ list_columns[counter] +' TO '+  column_name.lower() +';')
                    if data_type == 'varchar':
                        with connection.cursor() as cursor:
                            cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + '''
                                            ALTER COLUMN ''' + column_name.lower() + ' TYPE ' + data_type + '(' + column_len + ') ; ''')
                    else:
                        with connection.cursor() as cursor:
                            cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + '''
                                            ALTER COLUMN ''' + column_name.lower() + ' TYPE ' + data_type +'(' + column_len + ',0) '
                                            'USING ' + column_name.lower() + ' :: ' + data_type+'; ''')
                    messages.success(request, column_name.upper()+ " was changed")
                    logging.debug('old columns was changed')
                except(TypeError):
                    messages.warning(request, column_name.upper()+ " has no changes")
                    logging.debug('old columns wasnt changed')
                counter += 1
            counter = 1
            max_length = 15 - len(list_columns)
            while(counter < max_length):
                dim_name_attr = request.POST.get('Dname')
                dim_name_attr_new = request.POST.get('Dname')
                column_name = request.POST.get('input'+str(counter))
                dim_dt_attr = request.POST.get('input_dt'+str(counter))
                dim_len_attr = request.POST.get('input_len'+str(counter))
                logging.debug(column_name)
                if column_name != '':
                    print('-----------#---------')
                    print(dim_dt_attr)
                    print(dim_len_attr)
                    print(column_name)
                    column_1 = column_2
                    if column_1 and column_name is not None and dim_dt_attr is not None and dim_len_attr is not None:
                        try:
                            print('try')
                            dim_name = column_1.replace(' ', '_')
                            if dim_dt_attr == 'character':
                                data_type = 'varchar'
                            if dim_dt_attr == 'integer':
                                data_type = 'numeric'
                            #future update add max len of attribute
                            with connection.cursor() as cursor:  # add new column to db table
                                cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + ''' 
                                ADD ''' + str(column_name).replace(' ','_').lower() + ' '+ data_type+'('+ dim_len_attr +') ''')
                                messages.success(request, column_name.upper()+ " was added")
                        except (TypeError,ValueError):
                                messages.warning(request, column_name.upper()+ " already exsist")
                        except ProgrammingError:
                                messages.error(request,"Error! No dublicates in Attributes are allowed")
                    else:
                        logging.debug("not all field are feeled")
                    dim = dimension.replace(' ', '_')
                    sql_string = '''select column_name from information_schema.columns where table_name='engine_app_''' + dim.lower() + '''' '''
                counter +=1

            if dim_name_attr:
                dimension = dim_name_attr
#########################################################################################################################
        if 'delete_dim_111' in request.POST: #delete dimension
            dim_name_1 = request.POST.get('delete_dim')
            print(str(dim_name_1))
            try:
                print('try')
                print(list_default_dim)
                if str(dim_name_1) not in str(list_default_dim):
                    Dimensions.objects.filter(dimensionName=str(dim_name_1)).delete()

                    messages.success(request, dim_name_1.upper() + " was deleted")
                else:
                    messages.warning(request, dim_name_1.upper() + " is a default dimension and cant be deleted")
            except (ProgrammingError, TypeError):
                messages.warning(request,"Error! " +dim_name_1.upper() + " cant be deleted")
#########################################################################################################################
        if 'delete_dim' in request.POST:#delete the chosen fields from table
            if 'check' in request.POST:
                id = request.POST.getlist('check')
                dim_name_1 = request.POST.get('delete_dim')
                print('checked ' + str(id))
                print(dim_name_1)
                if str(dim_name_1) not in list_dimensions and str(dim_name_1) not in list_custom_dim:
                    p = Dimensions.objects.filter(new_name=str(dim_name_1)).values('id')  # change custom 1 to attribute!!!!
                    a = str(p)
                    key = int(''.join([i for i in a if i.isdigit()]))
                    c = Dimensions.objects.get(id=key)
                    g = c.dimensionName
                    dimension_name = g  # so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                    dim_name_1 = g
                try:
                    print('try_this')
                    dim_name = dim_name_1.replace(' ', '_')
                    print(dim_name.lower())
                    for i in range(len(id)):
                        with connection.cursor() as cursor:  # add new column to db table
                            cursor.execute('''ALTER TABLE engine_app_'''+dim_name.lower()+''' DROP COLUMN '''+id[i])
                            messages.success(request, "Item  " + str(id[i]) + " was deleted")
                except (ProgrammingError, TypeError):
                    if str(id[i]) is None:
                        messages.warning(request, "Item  " + str(id[i]) + " cant be deleted.")
                    else:
                        messages.warning(request, "Empty fields was checked to delete.")
            else:
                messages.warning(request, "You need to chose items to delete first")
#insert np list item to my_list
    for i in range(1,list_np.__len__()):
        my_list.append(list_np.item(i).lower())

    context = {
        'obj': obj,
        'dimension': dimension_name,
        'obj_event': obj_event,
        'list_column': my_list,
        'submit_fields': column_1,
        'list_default_dim': list_default_dim,
        'list_np_dt': list_np_dt

    }
    return render(request, 'master_data.html', context)
#########################################################################################################################
@login_required(login_url='user_login')
def import_master_d(request):
    f = ''
    df = ''
    df1 = ''
    lst_h = ''
    dim = ''
    dimension = ''
    list_header = []
    list_import_df = []
    list_import_dim = []
    obj_dim_name = Dimensions.objects.all().order_by('id')

    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')
        if 'dimension' in request.POST:
            logging.debug('dimension------------')
            dimension = request.POST.get('dimension')
            logging.debug(dimension)

        try:
            if 'import' in request.POST and  request.FILES['file_im']:
                f = request.FILES['file_im']
                option = request.POST.get('dim_name')
                dimension = option
                logging.debug(option)
                if option != ['']:
                    logging.debug(str(option) +' select options')
                    dim = conver_right_formt_of_tbl_name(option)
                    file_name = default_storage.save(f.name, f)
                    try:
                        df = pd.read_excel(f, "Sheet1", header=0, nrows=10)  # read only 10 rows to browse the file
                        np1 = np.array(df)
                        df["code"] = df.code.map("{:04}".format)
                        df1 = df.to_records(index=False)
                        cursor = connection.cursor()
                        sql_string = '''select column_name from information_schema.columns where table_name='engine_app_''' + dim.lower() + '''' '''
                        cursor.execute(sql_string)
                        sql_header = cursor.fetchall()
                        logging.debug(sql_header)
                        list_header = np.array([str(x) for x, in sql_header])
                        logging.debug(list_header)
                    except(XLRDError):
                        default_storage.delete(file_name)  # delete file
                        messages.error(request, 'The Sheet name of your file must be \'Sheet1\' ')
                else:
                    messages.error(request, 'Error!The destination table was not chosen')

            if 'submit' in request.POST:
                logging.debug('import')
                v = request.POST.getlist('index_df_col')  # getting index of columns names
                p = request.POST.getlist('df_names')  # geting columns names
                f = request.POST.get('f')  # we need also to get file name that was loaded.
                tbl_n = request.POST.get('dim')
                logging.debug(tbl_n)
                cursor = connection.cursor()
                sql_string = '''select column_name from information_schema.columns where table_name='engine_app_''' + tbl_n.lower() + '''' '''
                cursor.execute(sql_string)
                sql_header = cursor.fetchall()
                logging.debug(sql_header)
                list_header = np.array([str(x) for x, in sql_header])
                new_list_h = np.array(list_header)
                logging.debug(new_list_h)
                k_lst = []
                for i in range(1,len(new_list_h)):
                    k = request.POST.get('dim_option_'+str(i))  # getting dimensions
                    k_lst.append(k)
                v_p_k = np.column_stack((v, p, k_lst))  # set 3 list to one to save to compare it and save needed data to model
                logging.debug(v_p_k)
                for i in range(len(v_p_k)):
                    if v_p_k[i, 2] == '-none-':  # if none do nothing
                        logging.debug('Empty Select field')
                    if v_p_k[i,2] in new_list_h[1:]:#if item in dim list add it to lists
                        logging.debug('Not Empty Select field')
                        list_import_df.append(v_p_k[i,1])
                        list_import_dim.append(v_p_k[i,2])
                    if v_p_k[i, 2] not in new_list_h[1:] and v_p_k[i, 2] in list_custom_dim and v_p_k[i, 2] != '-none-':
                        list_import_df.append(v_p_k[i, 1])
                        list_import_dim.append(v_p_k[i, 2])
                # the point is to open the imported file in the end of logik to save time for posible mistake by chosing relations
                try:
                    file = default_storage.open(f)  # opening the uploaded file
                    table_name = tbl_n.lower()
                    df = pd.read_excel(file, "Sheet1", header=0)
                    df["code"] = df.code.map("{:04}".format)
                    # need to add progress bar
                    data = df[
                        df.columns.intersection(list_import_df)]  # get from dataFrame only needed columns from post request
                    data_list = data.values.tolist()  # convert df to values list
                    try:
                        with connection.cursor() as cursor:  # add new column to db table
                            cursor.execute('''TRUNCATE TABLE engine_app_''' + tbl_n.lower() + ''' RESTART IDENTITY;''')
                            logging.debug('delete all items')
                            insert_in_db(list_import_dim, data_list,
                                         table_name)  # function to insert data to data base(functions are on bottom)
                        file.close()  # before delting the file we need to close it
                        default_storage.delete(f)  # delete file
                        df = pd.DataFrame()
                    except(DataError):
                        file.close()
                        messages.error(request, "Error!Code field is required field and must compare the format "
                                                "of four digits and no double select of option is allowed")
                    except(ProgrammingError):
                        messages.error(request,'Error!Multiple selection of option fields or no option was selected')
                except FileNotFoundError:
                    file.close()
                    messages.error(request,"Error!First choose the file please")

        except(MultiValueDictKeyError ):
            messages.error(request,"ERROR! Choose the file and destination table please")


    context = {

        'obj_dim_name': obj_dim_name,
        'df1':df1,
        'df_head':list(df),
        'list_header':list_header[1:],
        'dim':dim,
        'f': f,
        'dimension':dimension
    }
    return render(request, 'import_master_d.html', context)



@login_required(login_url='user_login')
def brows_master_t(request):
    obj_dim_name = Dimensions.objects.all().order_by('id')
    option = ''
    dim_name = ''
    list_np = ''
    var_db = ''
    dim_browse_md = ''
    list_np_dt = []
    list_var = []
    i = 0
    var_template = ''
    now = datetime.now()

    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')
        if 'dimension' in request.POST:
            logging.debug('select master')
            option = request.POST.get('dimension')  # get the selected option and set it as table name
            temporar = str(option)
            dim_browse_md = temporar
            var_db = temporar.replace(' ', '_')  # 1.1 replace char to set right format of db table name
            var_template = temporar.replace('_', ' ')
            if str(option) not in list_default_dim and str(option) not in list_custom_dim:
                p = Dimensions.objects.filter(new_name=str(option)).values('id')  # change custom 1 to attribute!!!!
                a = str(p)
                key = int(''.join([i for i in a if i.isdigit()]))
                c = Dimensions.objects.get(id=key)
                g = c.dimensionName
                #so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                dim_name = g
                print(str(dim_name)+ ' not in both lists')
                var_db = str(dim_name).replace(' ','_')
            if str(option) not in list_default_dim and str(option) in list_custom_dim:
                #so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                print(str(dim_name)+ ' in custom list')
                p = Dimensions.objects.filter(dimensionName=str(dim_name)).values('id')  # change custom 1 to attribute!!!!
                a = str(p)
                key = int(''.join([i for i in a if i.isdigit()]))
                c = Dimensions.objects.get(id=key)
                g = c.new_name
                dimension_name = g  # so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                print(g)
                print(dimension_name)
                var_db = str(dimension_name).replace(' ','_')
            else:
                var_db = var_db

            cursor = connection.cursor()
            # SQL code to return columns from table
            sql_string = '''select * from engine_app_''' + var_db.lower()
            print(sql_string)
            sql_string_header = '''select column_name from information_schema.columns where table_name='engine_app_''' + var_db.lower() + '''' '''
            cursor.execute(sql_string)
            sql_columns = cursor.fetchall()
            cursor.execute(sql_string)
            list_np = np.array(sql_columns)
            # SQL code to return columns from table
            sql_data_type = '''SELECT column_name, character_maximum_length, numeric_precision
                                                FROM information_schema.columns
                                                WHERE table_schema = 'public'
                                                AND table_name   = 'engine_app_''' + var_db.lower() + '\' and column_name <> \'id\';'''

            cursor.execute(sql_data_type)
            sql_data_t = cursor.fetchall()
            list_np_dt = np.array(sql_data_t)
            logging.debug('list_np_dt-----------')
            logging.debug(list_np_dt)
            if (len(list_np) > 0):
                list_np = np.delete(list_np, [0], axis=1)
                logging.debug(list_np)
            cursor.execute(sql_string_header)
            sql_columns_header = cursor.fetchall()
            list_header = np.array(sql_columns_header)
            for i in range(list_header.__len__()):
                logging.debug(list_header.item(i))
                if (list_header.item(i) != 'id'):
                    list_var.append(list_header.item(i))
            logging.debug('----------')
            logging.debug(list_var)


        if 'delete' in request.POST:
            logging.debug('delete')
            if 'check' in request.POST:
                id = request.POST.getlist('check')
                dim = request.POST.get('dim')
                list_l = request.POST.getlist('list_np')
                logging.debug(dim)
                logging.debug(len(list_l))
                logging.debug('checked ' + str(id[0]))
                logging.debug(id)
                try:
                    logging.debug('try')
                    logging.debug('length of list '+str(len(id)))
                    if len(list_l) > len(id):
                        for i in range(len(id)):
                            logging.debug(id[i])
                            with connection.cursor() as cursor:  # add new column to db table
                                cursor.execute('''DELETE FROM engine_app_'''+dim.lower()+''' WHERE code = \''''+ id[i]+'''' ''')
                                logging.debug('delete item')
                                messages.success(request, "Item with id " + str(id[i]) + " was deleted")
                    else: #when all data must be deleted.delete all data and reset id increment to 0
                        with connection.cursor() as cursor:  # add new column to db table
                            cursor.execute('''TRUNCATE TABLE engine_app_''' + dim.lower() + ''' RESTART IDENTITY;''')
                            logging.debug('delete all items')
                            messages.success(request, "All item was deleted")
                except ():
                    messages.warning(request, "Item with id " + str(id[i]) + " cant be deleted")

            option = ''
        # -----------------------------------------------------------------------------------------------------------------------#
        if 'save' in request.POST:#
            logging.debug('save')
            tbl = request.POST.getlist('td_table')
            lst_h = request.POST.getlist('list_header')
            old_data = request.POST.getlist('td_tbl_old')
            old_data_1 = request.POST.getlist('td_table_old')
            dim = request.POST.get('dim')
            length = request.POST.getlist('length')
            d_t = request.POST.getlist('d_t')
            logging.debug(tbl)#new data
            logging.debug(length)#length of variables
            logging.debug(d_t)#data type
            logging.debug(lst_h)
            logging.debug(dim)
            logging.debug(old_data)#old data
            logging.debug(old_data_1)
            logging.debug(len(tbl))
            logging.debug(len(lst_h))

            #for i in range
            try:
                increment = int(len(old_data) / len(lst_h))  #
                logging.debug(increment)
                f = np.array(old_data).reshape(increment, len(lst_h))
                e = [i[0] for i in f]
                logging.debug(e)#list with 'code' field only .this must be compared with new iput whenn old input data is disabled.
            except(TypeError,ZeroDivisionError ):
                messages.error(request, 'ERROR!You didnt chose the Table.Choose Table first')

            if len(lst_h) > 0:
                if len(old_data) > 0:
                    logging.debug('table was with data')
                    try:
                        a = tbl
                        increment = int(len(tbl) / len(lst_h))
                        b = np.array(a).reshape(increment, len(lst_h))#reshape list to 2d array
                        logging.debug(b)
                        logging.debug(set(tbl))
                        c = tuple(b)
                        print(c)
                        d = [i[0] for i in b]
                        logging.debug(set([x for x in d if e.count(x) > 1]))
                        g = set([x for x in d if e.count(x) > 1])
                    except(ZeroDivisionError ):
                        messages.error(request, 'DivisionByZero Error')
                    except(TypeError ):
                        messages.error(request, 'Chose Table first')
                    #cursor = connection.cursor()
#------------------------------------------------------------------------------------------------------------------------
                    if tbl[0] in g:
                        messages.error(request, 'Code KEY dublicate Error! Code field cant have a dublicates')

                    if len(d) != len(set(d)):#check if dublicates in new input data
                        messages.error(request, 'Code KEY dublicate Error! Code field cant have a dublicates')

                    else:
                        #check if in new input containe dublicates
                        for i in range(len(c)):
                            for j in range(len(c[0])):
                                if d_t[j] == 'num':
                                   if not str(c[i][j]).isnumeric():
                                       messages.error(request, 'Error!Integer data type must have numeric value!')
                                if len(c[i][j]) > int(length[j]):
                                    messages.error(request, 'Error!Length of input value is to big!')
                        try:
                            with connection.cursor() as cursor:  # add new column to db table
                                cursor.execute(
                                    '''TRUNCATE TABLE engine_app_''' + dim.lower() + ''' RESTART IDENTITY;''')
                                logging.debug('delete all items')
                            insert_in_db(lst_h,c,dim.lower())
                            messages.success(request,'Data was successfully saved')
                        except(DataError):
                            messages.error(request,'Wrong data type in input.Insert data in right fotmat and length')
                        except(UnboundLocalError ):
                            messages.error(request, 'Chose Table first')
                else:
                    logging.debug('table was empty')
                    try:
                        increment = int(len(tbl) / len(lst_h))  #
                        a = tbl
                        b = np.array(a).reshape(increment, len(lst_h))
                        logging.debug(b)
                        c = tuple(b)
                        d = [i[0] for i in b]#list of inputs with first index only
                        logging.debug(d)
                        logging.debug(set([x for x in d if d.count(x) > 1]))#set of list d to check for dublicates
                    except(ZeroDivisionError ):
                        messages.error(request, 'DivisionByZero Error')
                    #except(TypeError ):
                        #messages.error(request, 'Chose Table first')
                    cursor = connection.cursor()
                    if len(tbl)> 0 and '' not in d:
                        logging.debug('tbl is not empty')
                        if len(d) != len(set(d)):
                            messages.error(request, 'Code KEY dublicate Error! Code field cant have a dublicates')
                            logging.debug('tbl in d '+str(tbl[i]))
                        else:
                            logging.debug('no dublicates detected')
                            # check if in new input containe dublicates
                            for i in range(len(c)):
                                for j in range(len(c[0])):
                                    if d_t[j] == 'num':
                                        if not str(c[i][j]).isnumeric():
                                            messages.error(request, 'Error!Integer data type must have numeric value!')
                                    if len(c[i][j]) > int(length[j]):
                                        messages.error(request, 'Error!Length of input value is to big!')
                            try:
                                with connection.cursor() as cursor:  # add new column to db table
                                    cursor.execute(
                                        '''TRUNCATE TABLE engine_app_''' + dim.lower() + ''' RESTART IDENTITY;''')
                                    logging.debug('delete all items')
                                insert_in_db(lst_h,c,dim.lower())
                                messages.success(request,'Data was successfully saved')
                            except(DataError):
                                messages.error(request,'Wrong data type in input.Insert data in right fotmat and length')
                            except(UnboundLocalError ):
                                messages.error(request, 'Chose Table first')
                    else:
                        messages.warning(request, 'No changes detected')

        if 'export' in request.POST:
            logging.debug('export_master_d')
            option = request.POST.get('dim')  # get the selected option and set it as table name
            logging.debug(option)
            obj_dim = Dimensions.objects.all().values_list('dimensionName')
            var_db = conver_right_formt_of_tbl_name(option)
            cursor = connection.cursor()
            # SQL code to return columns from table
            sql_string = '''select * from engine_app_''' + var_db.lower()
            sql_string_header = '''select column_name from information_schema.columns where table_name='engine_app_''' + var_db.lower() + '''' '''
            cursor.execute(sql_string)
            sql_columns = cursor.fetchall()
            cursor.execute(sql_string_header)
            sql_header = cursor.fetchall()
            logging.debug(sql_columns)
            logging.debug(sql_header)
            list_np_export = np.array(sql_columns)
            list_np_export_h = np.array([str(x) for x, in sql_header])
            logging.debug(list_np_export_h[1:])
            logging.debug(list_np_export[1:])
            if len(list_np_export) > 0:
                list_np_ex = np.vstack((list_np_export_h, list_np_export))
                logging.debug(list_np_ex)
                #converting numpy array into data frame to export as xlsx file
                df = pd.DataFrame(data=list_np_ex[1:, 1:],  # values
                index = list_np_ex[1:, 0],  # 1st column as index
                columns = list_np_ex[0, 1:])  # 1st row as the column names
            else:
                list_empty = []
                for i in range(len(list_np_export_h)):
                    list_empty.append('')
                logging.debug('-----ddd----------')
                logging.debug(list_empty)
                list_np_ex = np.vstack((list_np_export_h, list_empty))
                logging.debug(list_np_ex)
                # converting numpy array into data frame to export as xlsx file
                df = pd.DataFrame(data=list_np_ex[1:, 1:],  # values
                                  index=list_np_ex[1:, 0],  # 1st column as index
                                  columns=list_np_ex[0, 1:])  # 1st row as the column names
            logging.debug(df)
            a = ''
            b = ''
            b = str(var_db).replace('_',' ')
            if b in list_custom_dim:
                a =  var_db
            else:
                a = var_db
            try:
                os.mkdir(path)
            except OSError:
                logging.debug("Creation of the directory %s failed" % path)
            else:
                logging.debug("Successfully created the directory %s " % path)
            df.to_excel(r'C:\Users\\'+username+'\Desktop\Engine\\' + a.lower() + '_' + now.strftime(
                    "%Y%m%d_%H%M%S") + '.xlsx', index=False)
            var_db = ''
            messages.success(request, "Export file was saved on your Desktop.")

    context = {
        'obj_dim_name': obj_dim_name,
        'list_np': list_np,
        'var_template': var_template,
        'list_header': list_var,
        'option': var_db,
        'title': option,
        'dim_browse_md':dim_browse_md,
        'list_np_dt':list_np_dt,


    }

    return render(request, 'brows_master_t.html', context)

@login_required(login_url='user_login')
def define_master_t(request):
    obj_dim_name = Dimensions.objects.all()
    chosen_dim = ''
    temporar = ''
    list_np = []
    list_var = []
    sql_string_header = ''
    var_template = ''
    i = 0
    m = Dimensions()
    print('type of something')
    print(type(m.dimensionName))
    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')
        if 'select' in request.POST:
            option = request.POST.getlist('select')#get the selected option and set it as table name
            tempo = str(option)
            var_db_tbl = conver_right_formt_of_tbl_name(option)
            var_template = ''.join(
                [i for i in tempo if
                 i.isalpha() or i == ' '])  # replace to set right format for dim. name in template
            cursor = connection.cursor()
            # SQL code to return columns from table
            sql_string = '''select * from engine_app_''' + var_db_tbl.lower()
            print(sql_string)
            sql_string_header = '''select column_name from information_schema.columns where table_name='engine_app_''' + var_db_tbl.lower() + '''' '''
            cursor.execute(sql_string)
            sql_columns = cursor.fetchall()
            list_np = np.array(sql_columns)
            if(len(list_np) > 0):
                list_np = np.delete(list_np,[0], axis=1)
                logging.debug(list_np)
            cursor.execute(sql_string_header)
            sql_columns_header = cursor.fetchall()
            list_header = np.array(sql_columns_header)
            logging.debug('-------------')
            for i in range(list_header.__len__()):
                logging.debug(list_header.item(i))
                if(list_header.item(i) != 'id'):
                    list_var.append(list_header.item(i))
            logging.debug('----------')
            logging.debug(list_var)

        if 'save_t' in request.POST:
            list_of_data = request.POST.getlist('data')#get list of inputs
            header_dim = request.POST.getlist('header_dim')#get header of table
            option = request.POST.get('table_name')
            old_data = request.POST.getlist('old_data')
            logging.debug(old_data)
            table_name = conver_right_formt_of_tbl_name(option)
            logging.debug(list_of_data)
            logging.debug(list_of_data[0])
            logging.debug(header_dim)
            logging.debug(table_name)
            logging.debug(set(list_of_data))
            if len(header_dim) > 0:
                try:
                    increment = int(len(list_of_data) / len(header_dim))  #
                    a = list(list_of_data)
                    # a_1 = list(old_data)
                    b = np.array(a).reshape(increment, len(header_dim))
                    # b_1 = np.array(a).reshape(increment, len(header_dim))
                    logging.debug(b)
                    logging.debug(b[0,0])
                    logging.debug(set(list_of_data))
                    c = tuple(b)
                    print(c)
                    d = [i[0] for i in b]
                    logging.debug(set([x for x in d if d.count(x) > 1]))
                except(ZeroDivisionError ):
                    messages.error(request, 'DivisionByZero Error')
                except(TypeError ):
                    messages.error(request, 'Chose Table first')
                cursor = connection.cursor()
                if list_of_data[0] in old_data:
                    messages.error(request, 'Code KEY dublicate Error! Code cant have a dublicates')
                else:
                    while(i < len(b)):
                        if b[i,0] in set([x for x in d if d.count(x) > 1]):
                            logging.debug(b[i,0])
                            i +=1
                            messages.error(request, 'Code KEY dublicate Error! Code cant have a dublicates')
                        else:
                            try:
                                insert_in_db(header_dim,c,table_name)
                                i = len(b)
                                messages.success(request,'Data was successfully saved')
                            except(DataError):
                                messages.error(request,'Wrong data type in input.Insert data in right fotmat')
                            except(UnboundLocalError ):
                                messages.error(request, 'Chose Table first')
    context = {
        'obj_dim_name': obj_dim_name,
        'list_np':list_np,
        'var_template': var_template,
        'list_header': list_var,

    }
    return render(request, 'define_master_t.html', context)

@login_required(login_url='user_login')
def mapping_data(request):
    # attributes
    dimension = ''
    dimension_name = ''
    dim_name_attr = ''
    column_1 = ''
    my_list = []
    list_np = []
    list_np_dt = []
    list_new_name = []
    list_new_name_t = []
    list_dimensions = ['mapping t 1', 'mapping t 2', 'mapping t 3', 'mapping t 4',
                       'mapping t 5', 'mapping t 6', 'mapping t 7', 'mapping t 8', 'mapping t 9', 'mapping t 10']
    sql_data_type = ''
    dim_name_attr_old = ''
    # objects
    Mapping_Data.objects.all().order_by('id')
    data_type = Mapping_Data._meta.get_field('name').get_internal_type()
    #obj_event = Reporting_Event.objects.all()
    obj = Mapping_Data.objects.all().order_by('id')
    if request.method == 'POST':
        if 'logout_btn' in request.POST:
            logout(request)
            logging.debug('user loged out')
            return redirect('user_login')

        if 'dimension' in request.POST or 'add_rule' in request.POST:
            logging.debug('dimension')
            dim_name = request.POST.get('dimension')
            if dim_name is not None:
                dim_name_check = dim_name
                dim_name_attr_old = dim_name
                # dimname equals input of dimension.so new_name must object od dimension
                if str(dim_name_check) not in list_dimensions:
                    p = Mapping_Data.objects.filter(new_name=str(dim_name)).values('id')  # change custom 1 to attribute!!!!
                    a = str(p)
                    logging.debug(str(a) + ' ---------')
                    key = int(''.join([i for i in a if i.isdigit()]))
                    c = Mapping_Data.objects.get(id=key)
                    g = c.name
                    dimension_name = g  # so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                    dim_name = g
                    print(str(dim_name) + ' not in both lists')
                if str(dim_name_check) not in list_dimensions and str(dim_name_check) in list_custom_dim:
                    # dim_name = g#so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                    print(str(dim_name) + ' in custom list')
                    p = Mapping_Data.objects.filter(name=str(dim_name)).values(
                        'id')  # change custom 1 to attribute!!!!
                    a = str(p)
                    print(a)
                    key = int(''.join([i for i in a if i.isdigit()]))
                    c = Dimensions.objects.get(id=key)
                    g = c.new_name
                    dimension_name = g  # so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                    print(g)

                if dim_name:
                    dimension = dim_name
                    dim = dimension.replace(' ', '_')
                    cursor = connection.cursor()
                    # SQL code to return columns from table
                    sql_string = '''SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name   = 'engine_app_''' + dim.lower() + ''''; '''
                    sql_data_type = '''SELECT column_name, character_maximum_length, numeric_precision
                                                        FROM information_schema.columns
                                                        WHERE table_schema = 'public'
                                                        AND table_name   = 'engine_app_''' + dim.lower() + '\' and column_name <> \'id\';'''
                    cursor.execute(sql_string)
                    sql_columns = cursor.fetchall()
                    cursor.execute(sql_data_type)
                    sql_data_t = cursor.fetchall()
                    list_np = np.array(sql_columns)
                    list_np_dt = np.array(sql_data_t)
                    dimension_name = dim_name_attr_old  # in the end we need to show the new name,so we sett to attribute dimension the name of POST request
                    #########################################################################################################################
                    print(str(dimension_name) + ' get_dim name')

            else:
                dimension_name = 'New Mapping Table'
        if 'Dname11111' in request.POST:  # change name of custom dimensions
            logging.debug('Dname')
            dim_name = request.POST.get('submit_fields')
            dim_name_attr_old = dim_name
            column_1 = request.POST.get('Dname')
            print(str(dim_name_attr_old) + ' update dim name')
            print(column_1)
            if column_1 is not None:
                try:
                    print('try')
                    dim_tempo = column_1
                    dim_name_label = column_1.replace(' ', '_')
                    a = Mapping_Data.objects.values_list('new_name')

                    print(np.array(a))
                    list = np.array(a)
                    list_new_name_t = list
                    for i in range(list.__len__()):
                        if list.item(i) != None:
                            list_new_name.append(list.item(i))
                    print(list_new_name)
                    # with connection.cursor() as cursor:  # add new column to db table
                    print('try1')
                    eq = Mapping_Data.objects.filter(name=str(dim_tempo))
                    print(eq)
                    if str(dim_name_attr_old).lower() == str(column_1).lower() or str(
                            dim_name_attr_old).lower() == 'None':
                        messages.success(request, 'Name of Dimension ' + dim_name_label.upper() + " hade no chenges")
                    else:
                        for i in range(list_dimensions.__len__()):  # compare custom dim and add new name of custom dim
                            if str(dim_name_attr_old) == list_dimensions[
                                i]:  # check if dim name equals one of customs dim
                                p = Mapping_Data.objects.filter(name=str(list_dimensions[i])).values(
                                    'id')  # change custom 1 to attribute!!!!
                                a = str(p)
                                key = int(''.join([i for i in a if i.isdigit()]))
                                Mapping_Data.objects.filter(id=key).update(new_name=str(column_1))
                            if i < list_new_name.__len__() and str(dim_name_attr_old) == list_new_name[
                                i]:  # if not then custom was changed and the dim name comes from column new_name and must be compared
                                # if str(dim_name_attr_old) in list_new_name and str(dim_name_attr_old) == list_new_name[i]:
                                p = Mapping_Data.objects.filter(name=str(list_dimensions[i])).values('id')
                                a = str(p)
                                key = int(''.join([i for i in a if i.isdigit()]))
                                Mapping_Data.objects.filter(id=key).update(new_name=str(column_1))
                        messages.success(request, 'Name of Dimension ' + dim_name_label.upper() + " was changed")
                except (ProgrammingError):
                    messages.warning(request, 'Error! something goes wrong with save changes')
            #########################################################################################################################

        if 'save' in request.POST:
            next_mt = ''
            logging.debug('save')
            dim_name = request.POST.get('Dname')
            list_inputs = request.POST.getlist('input')
            list_dt = request.POST.getlist('input_dt')
            list_len = request.POST.getlist('input_len')
            logging.debug(dim_name)
            logging.debug(list_inputs)
            logging.debug(list_dt)
            logging.debug(list_len)
            obj = Mapping_Data.objects.all().order_by('id')
            logging.debug(obj[0].name)
            logging.debug(len(obj))
            dim_obj = Mapping_Data.objects.filter(new_name=str(dim_name).replace(' ','_'))
            logging.debug(len(dim_obj))
            #breakpoint()


            if dim_name != 'New Mapping Table':
                if len(dim_obj) < 1:
                    for j in range(1,len(obj)):
                        if obj[j].new_name is None:
                            logging.debug(obj[j].new_name)
                            logging.debug(j)
                            next_mt = obj[j].name
                            for i in range(len(list_inputs)):
                                if dim_name and list_inputs[i] is not None and list_dt[i] is not None and list_len[i] is not None:
                                    try:
                                        logging.debug('try')
                                        dim_name_f = obj[j].name.replace(' ', '_')
                                        if list_dt[i] == 'character':
                                            data_type = 'varchar'
                                        if list_dt[i] == 'integer':
                                            data_type = 'numeric'
                                        # future update add max len of attribute
                                        a = str(list_inputs[i]).replace(' ','_')
                                        a = a.replace('-','_')
                                        with connection.cursor() as cursor:  # add new column to db table
                                            logging.debug('''ALTER TABLE engine_app_''' + dim_name_f.lower() + ''' ADD ''' + a.lower() + ' ' + data_type + '(' +list_len[i] + ') ''')
                                            cursor.execute('''ALTER TABLE engine_app_''' + dim_name_f.lower() + ''' ADD ''' + a.lower() + ' ' + data_type + '(' +list_len[i] + ') ''')
                                            messages.success(request, list_inputs[i].upper() + " was added")
                                    except (TypeError, ValueError):
                                        messages.warning(request, list_inputs[i].upper() + " already exsist")
                                else:
                                    logging.debug("not all field are feeled")
                            obj[j].new_name = dim_name
                            obj[j].save()
                            break
                else:
                    messages.error(request, 'Error!Mapping Table '+dim_name+' already exist')

            else:
                messages.error(request,'Error!Please change default Mapping name.')
            logging.debug('im out of loop')
            logging.debug(next_mt)



        if 'apply' in request.POST:  # add columns to dimension and save changes
            logging.debug('apply')
            column_2 = request.POST.get('dimension_to_dlt')
            column_3 = request.POST.get('Dname')
            list_columns = request.POST.getlist('list_np_dt')
            logging.debug(str(column_2) + ' submit fields')
            logging.debug(str(column_3) + ' Dname')
            logging.debug(list_columns)
            # change the custom dimension to old name
            try:
                if str(column_2) not in list_dimensions:
                    p = Mapping_Data.objects.filter(new_name=str(column_2)).values(
                        'id')  # change custom 1 to attribute!!!!
                    print(p)
                    a = str(p)
                    print(a + ' id')
                    key = int(''.join([i for i in a if i.isdigit()]))
                    c = Mapping_Data.objects.get(id=key)
                    g = c.name
                    dimension_name = g  # so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                    column_2 = g
                    Mapping_Data.objects.filter(id=key).update(new_name=str(column_3))
            except(TypeError, ValueError):
                messages.warning(request, "Error! change cant be done")


            # # change columns are allready exsists
            list_inputs = request.POST.getlist('input')
            # list_dt = request.POST.getlist('input_dt')
            # list_len = request.POST.getlist('input_len')
            # logging.debug(dim_name)
            # logging.debug(list_inputs)
            # logging.debug(list_dt)
            # logging.debug(list_len)
            # for i in range(len(list_inputs)):
            #     logging.debug('incert new columns')
            #     if dim_name and list_inputs[i] is not None and list_dt[i] is not None and list_len[i] is not None:
            #         try:
            #             logging.debug('try')
            #             dim_name = column_3.name.replace(' ', '_')
            #             if list_dt[i] == 'character':
            #                 data_type = 'varchar'
            #             if list_dt[i] == 'integer':
            #                 data_type = 'numeric'
            #             if list_inputs[i] != list_columns[i]:
            #                 with connection.cursor() as cursor:
            #                     cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + '''
            #                             RENAME COLUMN ''' + list_columns[i] + ' TO ' + list_inputs[i].lower() + ';')
            #             if data_type == 'varchar':
            #                 with connection.cursor() as cursor:
            #                     cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + '''
            #                                             ALTER COLUMN ''' + list_inputs[i].lower() + ' TYPE ' + data_type + '(' + list_len[i] + ') ; ''')
            #             else:
            #                 with connection.cursor() as cursor:
            #                     cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + '''
            #                                             ALTER COLUMN ''' + list_inputs[i].lower() + ' TYPE ' + data_type + '(' + list_len[i] + ',0) '
            #                                                                                                                                'USING ' + list_len[i].lower() + ' :: ' + data_type + '; ''')
            #             messages.success(request, list_inputs[i].upper() + " was changed")
            #             logging.debug('old columns was changed')
            #
            #         except(TypeError):
            #             messages.warning(request, list_inputs[i].upper() + " has no changes")
            #             logging.debug('old columns wasnt changed')

            i = 0
            max_length = 15 - len(list_columns)
            for i in range(len(list_inputs)):
                logging.debug('add new fields---------------------------------------------------------')
                dim_name_attr = request.POST.get('Dname')
                dim_name_attr_new = request.POST.get('Dname')
                column_name = request.POST.getlist('input')
                dim_dt_attr = request.POST.getlist('input_dt')
                dim_len_attr = request.POST.getlist('input_len')
                print('-----------#---------')
                print(dim_dt_attr)
                print(dim_len_attr)
                print(column_name)
                column_1 = column_2
                if column_1 and column_name is not None and dim_dt_attr is not None and dim_len_attr is not None:
                    try:
                        print('try')
                        dim_name = column_1.replace(' ', '_')
                        if dim_dt_attr[i] == 'character':
                            data_type = 'varchar'
                        if dim_dt_attr[i] == 'integer':
                            data_type = 'numeric'
                        # future update add max len of attribute
                        a = column_name[i].replace(' ', '_').lower()
                        a = a.replace('-','_')
                        with connection.cursor() as cursor:  # add new column to db table
                            cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + '''
                                    ADD ''' + a.lower() + ' ' + data_type + '(' + dim_len_attr[i] + ') ''')
                            messages.success(request, column_name[i].upper() + " was added")
                    except (TypeError, ValueError ):
                        messages.warning(request, column_name[i].upper() + " already exsist")
                    except ProgrammingError:
                        messages.error(request,"Data Error!Check that fields are filled,no dublicates are in Attributes and Length field is a number.")
                    #except (ProgrammingError):
                        #messages.warning(request, "Error!Length must be a number")
                else:
                    logging.debug("not all field are feeled")
                dim = dimension.replace(' ', '_')
                sql_string = '''select column_name from information_schema.columns where table_name='engine_app_''' + dim.lower() + '''' '''
                logging.debug(i)
                i += 1

            counter = 0
            while (counter < len(list_columns)):
                column_name = request.POST.get('Dname_' + str(counter + 1))
                column_dt = request.POST.get('D_data_type_' + str(counter + 1))
                column_len = request.POST.get('D_length_' + str(counter + 1))
                logging.debug(column_name)
                logging.debug(column_dt)
                logging.debug(column_len)
                column_name = str(column_name).replace(' ','_')
                column_name = str(column_name).replace('-','_')
                try:
                    dim_name = column_2.replace(' ', '_')
                    logging.debug('try')

                    if column_dt == 'character':
                        data_type = 'varchar'
                    if column_dt == 'integer':
                        data_type = 'numeric'
                    # future update add max len of attribute
                    # add new column to db table

                    logging.debug(column_name)
                    logging.debug(list_columns)
                    logging.debug(counter)
                    logging.debug(list_columns[counter])
                    logging.debug(data_type)
                    logging.debug('''ALTER TABLE engine_app_''' + dim_name.lower() + '''
                                                        ALTER COLUMN ''' + column_name.lower() + ' TYPE ' + data_type + '(' + column_len + ',0) '
                                                                                                                                           'USING ' + column_name.lower() + ' :: ' + data_type + '; ''')
                    # äbreakpoint()

                    if column_name != list_columns[counter]:
                        with connection.cursor() as cursor:
                            cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + ''' 
                                        RENAME COLUMN ''' + list_columns[counter] + ' TO ' + column_name.lower() + ';')
                    if data_type == 'varchar':
                        with connection.cursor() as cursor:
                            cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + '''
                                                        ALTER COLUMN ''' + column_name.lower() + ' TYPE ' + data_type + '(' + column_len + ') ; ''')
                    else:
                        with connection.cursor() as cursor:
                            cursor.execute('''ALTER TABLE engine_app_''' + dim_name.lower() + '''
                                                        ALTER COLUMN ''' + column_name.lower() + ' TYPE ' + data_type + '(' + column_len + ',0) '
                                                                                   'USING ' + column_name.lower() + ' :: ' + data_type + '; ''')
                    messages.success(request, column_name.upper() + " was changed")
                    logging.debug('old columns was changed')
                except(TypeError):
                    messages.warning(request, column_name.upper() + " has no changes")
                    logging.debug('old columns wasnt changed')
                #except(ProgrammingError):
                #    messages.error(request,"Error!Dont use names that already exist in table.")
                counter += 1
            if dim_name_attr:
                dimension = dim_name_attr
            dimension_name = ''


            #########################################################################################################################
        if 'delete' in request.POST:  # delete dimension
            dim = ''
            dim_name = request.POST.get('dimension_to_dlt')
            logging.debug(dim_name)
            logging.debug(dim)
            try:
                dim_obj = Mapping_Data.objects.get(new_name=dim_name)
                dim = str(dim_obj.name).replace(' ','_')
                logging.debug(dim_obj.name)

                cursor = connection.cursor()
                sql_string = '''select column_name from information_schema.columns where table_name='engine_app_''' + dim.lower() + '''' '''
                logging.debug(sql_string)
                cursor.execute(sql_string)
                sql_columns = cursor.fetchall()
                list_np = np.array(sql_columns)
                logging.debug(list_np)
                for i in range(1,len(list_np)):
                    logging.debug(list_np[i].item())
                    with connection.cursor() as cursor:  # add new column to db table
                        cursor.execute('''ALTER TABLE engine_app_''' + dim.lower() + ''' DROP COLUMN ''' + list_np[i].item())
                logging.debug(dim_name)
                rule_obj = Mapping_Data.objects.get(
                    new_name=dim_name
                )
                rule_obj.new_name = None
                rule_obj.save()
                messages.success(request, 'Mapping Table -' + str(dim_name) + '- was deleted.')
            except Exception :
                messages.error(request,"No new Table to delete")
            #########################################################################################################################
        if 'delete_dim' in request.POST:  # delete the chosen fields from table
            if 'check' in request.POST:
                id = request.POST.getlist('check')
                dim_name_1 = request.POST.get('delete_dim')
                print('checked ' + str(id))
                print(dim_name_1)
                if str(dim_name_1) not in list_dimensions and str(dim_name_1) not in list_custom_dim:
                    p = Mapping_Data.objects.filter(new_name=str(dim_name_1)).values(
                        'id')  # change custom 1 to attribute!!!!
                    a = str(p)
                    key = int(''.join([i for i in a if i.isdigit()]))
                    c = Mapping_Data.objects.get(id=key)
                    g = c.name
                    dimension_name = g  # so we checked the field new_name and there is our new dim name,so we set to dim_name new dimension
                    dim_name_1 = g
                try:
                    print('try_this')
                    dim_name = dim_name_1.replace(' ', '_')
                    print(dim_name.lower())
                    for i in range(len(id)):
                        with connection.cursor() as cursor:  # add new column to db table
                            cursor.execute(
                                '''ALTER TABLE engine_app_''' + dim_name.lower() + ''' DROP COLUMN ''' + id[i])
                            messages.success(request, "Item  " + str(id[i]) + " was deleted")
                except (ProgrammingError, TypeError):
                    if str(id[i]) is None:
                        messages.warning(request, "Item  " + str(id[i]) + " cant be deleted.")
                    else:
                        messages.warning(request, "Empty fields was checked to delete.")
            else:
                messages.warning(request, "You need to chose items to delete first")
            # insert np list item to my_list
        for i in range(1, list_np.__len__()):
            my_list.append(list_np.item(i).lower())

    context = {
        'obj': obj,
        'dimension': dimension_name,
        #'obj_event': obj_event,
        'list_column': my_list,
        'submit_fields': column_1,
        'list_default_dim': list_default_dim,
        'list_np_dt': list_np_dt

    }

    return render(request, 'mapping_data.html', context)

@login_required(login_url='user_login')
def perform_the_data(request):
    obj = Log_Mapping_Performe.objects.all().order_by('id')
    obj_1 = Log_Reporting.objects.all().order_by('id')
    obj_2 = Mapping_Sets.objects.all().order_by('id')
    now = datetime.now()
    if 'logout_btn' in request.POST:
        logout(request)
        logging.debug('user loged out')
        return redirect('user_login')

    if 'run' in request.POST:
        end_dim = ''
        iteration_num = ''
        sql_string = ''
        sql_string_2 = ''
        sql_string_3 = ''
        sql_string_4 = ''
        obj_mapping_t_1 = ''
        mt_field_in_1 = ''
        mt_1 = ''
        dm_1 = ''
        dm_field_1 = ''
        mt_field_out_1 = ''
        dm_out_2 = ''
        obj_mapping_t_2 = ''
        mt_field_in_2 = ''
        mt_2 = ''
        dm_2 = ''
        dm_field_2 = ''
        mt_field_out_2 = ''
        dm_out_2 = ''
        obj_mapping_t_3 = ''
        mt_field_in_3 = ''
        mt_3 = ''
        dm_3 = ''
        dm_field_3 = ''
        mt_field_out_3 = ''
        dm_out_3 = ''
        input_l = []
        output_l = []
        list_to_dlt = []
        list_headers = []
        logging.debug('run')

        select = request.POST.getlist('select')
        logging.debug(select)
        check_dublicate = Log_Mapping_Performe.objects.filter(event=select[0], period=select[1])
        if len(check_dublicate) > 0:
            messages.error(request,"Error!Performence with event "+select[0]+" and period "+select[1]+" allready excist.")
        else:
            cursor = connection.cursor()
            # SQL code to return columns from table
            a = select[0]
            b = select[1]
            logging.debug("................................##")
            sql_str = '''select * from engine_app_imported_data where reporting_event = \'''' + a +'''\' and reporting_period = \''''+b+'''\''''
            logging.debug("................................")
            print(sql_str)
            cursor.execute(sql_str)
            sql_col = cursor.fetchall()
            cursor.execute(sql_str)
            list_np = np.array(sql_col)
            if (len(list_np) > 0):
                list_np = np.delete(list_np, [0], axis=1)
                #logging.debug(list_np)
            #logging.debug(list_np)
            logging.debug('here----------')
            list_default_header = ['reporting_event', 'reporting_period', 'entity', 'konto', 'partner', 'movement_type',
                                   'investe', 'document_type']
            list_def_betrag = ['value_in_lc','value_in_gc','value_in_tc','quantity']
            list_headers = list_default_header
            logging.debug('+++++++++++++++++++++++++')
            db_tbl_name = 'output_data'
            logging.debug(list_headers)
            data = pd.DataFrame(
                list_np)  # df[df.columns.intersection(list_np)]  # get from dataFrame only needed columns from post request
            logging.debug(data)
            data_list = data.values.tolist()  # convert df to values list
            logging.debug(data_list)
            x = list_headers + list_def_betrag
            logging.debug(x)
            insert_in_db(x, data_list, db_tbl_name)

            logging.debug(check_dublicate)
            obj_transaction_d = Imported_Data.objects.filter(reporting_event=str(select[0]), reporting_period=str(select[1])).values_list('konto')
            logging.debug(np.array(list(obj_transaction_d)))

            obj_set = Mapping_Sets.objects.get(setName=str(select[2]))
            logging.debug(obj_set.setName)
            obj_rule = Mapping_Rules.objects.filter(setName=obj_set.id).values_list('ruleName')
            obj_rule_key = Mapping_Rules.objects.filter(setName=obj_set.id, type='input').values_list('ruleName').distinct()
            logging.debug(obj_rule)
            logging.debug(obj_rule_key)
            iteration_num = len(obj_rule_key)
            logging.debug(iteration_num)
            logging.debug('wwwwwwwwwwwwwwww')
            #breakpoint()
            a = set(obj_rule_key)
            logging.debug(a)
            b = list(a)
            logging.debug(type(b))
            for c in range(len(obj_rule_key)):
                logging.debug('BEGIN OF SET ITEM: '+str(obj_rule_key[c]))
                obj_rule_in = Mapping_Rules.objects.filter(ruleName=obj_rule_key[c], setName=obj_set.id, type='input')#change to filter by more than one.update
                obj_rule_out = Mapping_Rules.objects.filter(ruleName=obj_rule_key[c], setName=obj_set.id, type='output')

                if len(obj_rule_out) > 0:
                    logging.debug('len_1')
                    mt_field_out_1 = obj_rule_out[0].mtField
                    dm_out_1 = str(obj_rule_out[0].dimensionName.new_name).replace(' ', '_')
                    logging.debug(mt_field_out_1)
                    logging.debug(dm_out_1)
                if len(obj_rule_out) > 1:
                    logging.debug('len_2')
                    mt_field_out_2 = obj_rule_out[1].mtField
                    dm_out_2 = str(obj_rule_out[1].dimensionName.new_name).replace(' ', '_')
                    logging.debug(mt_field_out_2)
                    logging.debug(dm_out_2)
                if len(obj_rule_out) > 2:
                    logging.debug('len_3')
                    mt_field_out_3 = obj_rule_out[2].mtField
                    dm_out_3 = str(obj_rule_out[2].dimensionName.new_name).replace(' ', '_')
                    logging.debug(mt_field_out_3)
                    logging.debug(dm_out_3)

                cursor = connection.cursor()
    #must work for multiple key but works only for one key
                if len(obj_rule_in) > 0:
                    logging.debug('len 1')
                    obj_mapping_t_1 = Mapping_Data.objects.get(id=str(obj_rule_in[0].mtName.id))
                    obj_mapping_t_1 = obj_mapping_t_1.name
                    mt_field_in_1 = obj_rule_in[0].mtField
                    mt_1 = str(obj_mapping_t_1).replace(' ', '_')
                    dm_1 = str(obj_rule_in[0].dimensionName.dimensionName).replace(' ', '_')
                    dm_field_1 = str(obj_rule_in[0].dimField).replace(' ', '_')
                    logging.debug(obj_mapping_t_1)
                    logging.debug(mt_field_in_1)

                if len(obj_rule_in) > 1:
                    logging.debug('len 2')
                    obj_mapping_t_2 = Mapping_Data.objects.get(id=str(obj_rule_in[1].mtName.id))
                    if obj_mapping_t_2 != '':
                        obj_mapping_t_2 = obj_mapping_t_2.name
                    mt_field_in_2 = obj_rule_in[1].mtField
                    mt_2 = str(obj_mapping_t_2).replace(' ', '_')
                    dm_2 = str(obj_rule_in[1].dimensionName.dimensionName).replace(' ', '_')
                    dm_field_2 = str(obj_rule_in[1].dimField).replace(' ', '_')
                    logging.debug(obj_mapping_t_2)
                    logging.debug(mt_field_in_2)

                if len(obj_rule_in) > 2:
                    logging.debug('len 3')
                    obj_mapping_t_3 = Mapping_Data.objects.get(id=str(obj_rule_in[2].mtName.id))
                    if obj_mapping_t_3 != '':
                        obj_mapping_t_3 = obj_mapping_t_3.name
                    mt_field_in_3 = obj_rule_in[2].mtField
                    mt_3 = str(obj_mapping_t_3).replace(' ', '_')
                    dm_3 = str(obj_rule_in[2].dimensionName.dimensionName).replace(' ', '_')
                    dm_field_3 = str(obj_rule_in[2].dimField).replace(' ', '_')
                    logging.debug(obj_mapping_t_3)
                    logging.debug(mt_field_in_3)
                    # creating a dinamyc sql query depends on mapping rule keys
                arr_keys = np.array([[[dm_1], [dm_field_1], [mt_1], [mt_field_in_1], [mt_field_out_1], [dm_out_1]],
                                     [[dm_2], [dm_field_2], [mt_2], [mt_field_in_2], [mt_field_out_2], [dm_out_2]],
                                     [[dm_3], [dm_field_3], [mt_3], [mt_field_in_3], [mt_field_out_3],
                                      [dm_out_3]]])  # create numpy array
                logging.debug('arr key old')
                logging.debug(arr_keys)
                list_to_dlt = []
                for i in range(len(arr_keys)):#check if row of keys is empty and delete it
                    logging.debug(len(arr_keys))
                    logging.debug(str(i)+'######')
                    #logging.debug(arr_keys[i][0])
                    #logging.debug(arr_keys[i][4])
                    #if
                    if arr_keys[i][0] == '' and arr_keys[i][4] == '':
                        list_to_dlt.append(i)
                logging.debug('list to delete++++++++++++++++++++')
                logging.debug(list_to_dlt)
                lst_1 = []
                lst_2 = []
                lst_3 = []
                lst_4 = []

                logging.debug('im here')
                for i in range(len(list_to_dlt),0,-1):
                    logging.debug(str(i) + ' this is i')
                    logging.debug(list_to_dlt[i-1])
                    arr_keys = np.delete(arr_keys, list_to_dlt[i-1], axis=0)
                logging.debug('arr_key new:')
                logging.debug(arr_keys)

                sql_sub_str = '''select engine_app_output_data.id,reporting_event,
                                                                                    reporting_period,
                                                                                    entity,
                                                                                    konto,
                                                                                    partner,
                                                                                    movement_type,
                                                                                    investe,
                                                                                    document_type,
                                                                                    value_in_lc,
                                                                                    value_in_gc,
                                                                                    value_in_tc,
                                                                                    quantity,
                                                                                    '''

                sql_sub_str_1 = '''engine_app_%s.%s as %s \n'''

                sql_sub_str_2 = ''' from engine_app_%s 
                                                                                    right join engine_app_output_data  
                                                                                    on '''
                sql_sub_str_3 = ''' engine_app_%s.%s = engine_app_output_data.%s\n'''
                sql_sub_str_4 = ''' where engine_app_output_data.reporting_event = \'%s\'
                                                                                and engine_app_output_data.reporting_period = \'%s\';'''
                sub_lst_1 = np.array([[mt_1, mt_field_out_1,dm_out_1.lower()],
                            [mt_2, mt_field_out_2, dm_out_2.lower()],
                            [mt_3, mt_field_out_3, dm_out_3.lower()]])

                sub_lst_2 = np.array([[mt_1, mt_field_in_1, dm_1.lower()],
                                      [mt_2,mt_field_in_2,dm_2.lower()],
                                      [mt_3,mt_field_in_3,dm_3.lower()]])

                sub_lst_3 = np.array([select[0], select[1]])

                logging.debug(len(obj_rule_in))
                logging.debug(len(obj_rule_out))
                for j in range(len(obj_rule_out)):
                    logging.debug(sql_string)
                    if j == len(obj_rule_out)-1:
                        logging.debug('j is 0')
                        sql_string = sql_string +  sql_sub_str_1
                    else:
                        sql_string = sql_string + sql_sub_str_1 + ','
                    lst_1 = np.array(sub_lst_1[j])
                    lst_4.append(lst_1)
                logging.debug(sql_string)

                for i in range(len(obj_rule_in)):
                    logging.debug(sql_string_2)
                    lst_2 = np.array(sub_lst_2[i])
                    lst_3.append(lst_2)
                    if i != 0:
                        sql_string_2 = sql_string_2 +' and'+ sql_sub_str_3
                    else:
                        sql_string_2 = sql_string_2 + sql_sub_str_3
                    logging.debug(sql_string_2)
                logging.debug('list_3---------------------')
                logging.debug(np.array(lst_3))
                logging.debug(np.array(lst_4))
                logging.debug(sql_string_2)

                sql_string = sql_sub_str+sql_string+sql_sub_str_2+sql_string_2+sql_sub_str_4
                logging.debug(sql_string)  # dinamyc sql query
                logging.debug('.........')
                logging.debug(np.concatenate((lst_1 ,np.array(mt_1), lst_3 ,sub_lst_3), axis=None))
                a = np.concatenate((lst_4 ,np.array(mt_1), lst_3 ,sub_lst_3), axis=None)
                logging.debug(a.tolist())
                b = a.tolist()
                logging.debug(tuple(b))
                c = tuple(b)
                logging.debug(c)

                logging.debug(sql_string % c)
                cursor.execute(sql_string % c)


                arr_keys =  np.array([[[dm_1],[dm_field_1],[mt_1],[mt_field_in_1],[mt_field_out_1],[dm_out_1]],
                                    [[dm_2],[dm_field_2],[mt_2],[mt_field_in_2],[mt_field_out_2],[dm_out_2]],
                                    [[dm_3],[dm_field_3],[mt_3],[mt_field_in_3],[mt_field_out_3],[dm_out_3]]])#create numpy array
                logging.debug(arr_keys)
                logging.debug(sql_string)



                # creating a dinamyc sql query depends on mapping rule keys

                sql_columns = cursor.fetchall()
                logging.debug('##############')
                logging.debug(sql_columns)
                list_np = np.array(sql_columns)

                logging.debug(list_np)#get output table as numpy array

                #with connection.cursor() as cursor:  # add new column to db table
                #    cursor.execute('''ALTER TABLE engine_app_output_data ADD ''' + str(dm_out_new).replace(' ', '_').lower() + ' varchar (255) ''')
                logging.debug(input_l)
                logging.debug(output_l)
                list_default_header = ['id','reporting_event', 'reporting_period', 'entity', 'konto', 'partner', 'movement_type',
                                       'investe', 'document_type']
                list_def_betrag = ['value_in_lc', 'value_in_gc', 'value_in_tc', 'quantity']
                list_headers = list_default_header
                logging.debug('+++++++++++++++++++++++++')
                for i in range(len(obj_rule_out)):
                    obj_dim = Dimensions.objects.get(id=obj_rule_out[i].dimensionName.id)
                    if obj_dim.dimensionName in list_default_dim:
                        end_dim = obj_dim.new_name
                    else:
                        end_dim = obj_dim.dimensionName
                    logging.debug(end_dim)
                    logging.debug(list_headers)
                    list_headers.append(str(end_dim).replace(' ','_').lower())
                db_tbl_name = 'output_data'
                np_array = np.array(list_headers)
                #logging.debug(np_array[9:])
                logging.debug('bbbbbbbbbbbbdddddddddddvvvvvvvvv')
                logging.debug(len(list_np[1]))
                len_list_np = len(list_np[1])-1
                logging.debug(list_headers)
                logging.debug(len(list_headers))
                logging.debug(len(list_default_header))
                end_column = len(list_headers)-9
                #end_column = len(list_np[1])-9 # update 10.12.2020
                logging.debug(str(end_column)+'--------------------')
                array_to_update = np.append(list_np[:, len_list_np:len_list_np+end_column], list_np[:, 0:1], axis=1)
                data = pd.DataFrame(array_to_update)#df[df.columns.intersection(list_np)]  # get from dataFrame only needed columns from post request
                logging.debug(array_to_update)
                logging.debug(data)
                logging.debug(end_column)
                logging.debug(list_np[:, 9:9+end_column])
                logging.debug(list_np[:, 0:1])
                logging.debug('..........,,,,,,,,,............')
                data_list = data.values.tolist()  # convert df to values list
                logging.debug(np_array[9:])
                x = list_headers
                logging.debug(x)
                logging.debug(db_tbl_name)
                #äbreakpoint()
                #insert_in_db(list_headers, data_list, db_tbl_name)
                #logging.debug(np_array[9:])
                #logging.debug(data_list)

                update_db(np_array[9:], data_list, db_tbl_name)
                #breakpoint()
                sql_string = ''
                sql_string_2 = ''
                sql_sub_str = ''
                sql_sub_str_1 = ''
                sql_sub_str_2 = ''
                sql_sub_str_3 = ''
                sql_sub_str_4 = ''
                lst_1 = []
                lst_2 = []
                lst_3 = []
                list_headers = []
            obj_log = Log_Mapping_Performe.objects.get_or_create(
                event = select[0],
                period = select[1],
                timestampImportD = datetime.now(tz=get_current_timezone()),#strftime("%Y-%m-%d %H:%M:%S"),
                setName = Mapping_Sets.objects.get(setName=select[2]),
                user=request.user,
             )

    if 'delete' in request.POST:
        logging.debug('delete')
        if 'check' in request.POST:
            id = request.POST.getlist('check')
            logging.debug(id)
            logging.debug('checked ' + str(id[0]))
            try:
                logging.debug('try')
                for i in range(len(id)):
                    a = Log_Mapping_Performe.objects.get(id=str(id[i]))
                    logging.debug(a.event)
                    logging.debug(a.period)
                    with connection.cursor() as cursor:  # add new column to db table
                        logging.debug(
                            '''DELETE FROM engine_app_output_data WHERE reporting_event = \'''' + a.event + '''\' AND reporting_period = \'''' + a.period + '''\'''')
                        cursor.execute(
                            '''DELETE FROM engine_app_output_data WHERE reporting_event = \'''' + a.event + '''\' AND reporting_period = \'''' + a.period + '''\'''')
                        cursor.execute('''DELETE FROM engine_app_log_mapping_performe WHERE id = ''' + id[i])
                        messages.success(request, "Item with id " + str(id[i]) + "was deleted")
            except ():
                messages.warning(request, "Item with id " + str(id[i]) + " cant be deleted")

    context = {
        'obj':obj,
        'obj_1':obj_1,
        'obj_2':obj_2
    }
    return render(request, 'Perform_the _data.html', context)


#FUNCTIONS--------------------------------------------------------------------------------------------------------------#
def get_id(model_N, field_N, field_V):
    p = model_N.objects.filter(new_name=str(field_V)).values('id')  # change custom 1 to attribute!!!!
    a = str(p)
    print(a)
    key = int(''.join([i for i in a if i.isdigit()]))
    c = Dimensions.objects.get(id=key)
    g = c.dimensionName
    return g

def insert_in_db(list_import_dimension,some_list,da_table_name):
    tmp = ''
    tmp_2 = ''
    table_name = str(da_table_name).replace(' ','_').lower()
    crsr = connection.cursor()
    crsr.fast_executemany = True
    for j in range(list_import_dimension.__len__()):  # create a dinamic values placeholder to sql query
        tmp += '%s,'
    for j in range(list_import_dimension.__len__()):  # create a dinamic column names for sql query
        tmp_2 += str(list_import_dimension[j]) + ','
    data_list = some_list  # convert df to list of values
    a = tmp_2.replace(' ', '_')  # need to write the name of table correct
    logging.debug(a)
    sql = '''INSERT INTO engine_app_'''+table_name+ '''(''' + a[:-1].lower() + ''') VALUES (''' + tmp[:-1] + '''); '''
    # extract column and convert to list of single-value tuples
    logging.debug(sql)
    logging.debug(data_list)
    crsr.executemany(sql, data_list)  # insert the query with list of data to db
    connection.commit()

def update_db(list_import_dimension,some_list,da_table_name):
    logging.debug('im in update db function')
    tmp = ''
    tmp_2 = ''
    np_arr = np.array(list_import_dimension)
    table_name = str(da_table_name).replace(' ','_').lower()
    crsr = connection.cursor()
    crsr.fast_executemany = True
    #for j in range(list_import_dimension.__len__()):  # create a dinamic values placeholder to sql query
    #    tmp += '%s,'
    #for j in range(list_import_dimension.__len__()):  # create a dinamic column names for sql query
    #    tmp_2 += str(list_import_dimension[j]) + ','
    data_list = some_list  # convert df to list of values
    #a = tmp_2.replace(' ', '_')  # need to write the name of table correct
    #sql = '''UPDATE engine_app_'''+table_name+ ''' SET (''' + a[:-1].lower() + ''') FROM (VALUES (''' + tmp[:-1] + '''))
    #        WHERE reporting_event = \''''+event+'''\' AND reporting_period = \''''+period+'''\'; '''
    sql_columns = ''
    sql_final = ''
    sql = ''' UPDATE engine_app_'''+table_name+''' SET '''
    sql_2 = " = %s"
    sql_3 = " WHERE id = %s"
    for i in range(len(list_import_dimension)):
        logging.debug(i)
        if i ==  len(list_import_dimension)-1:
            sql_columns = sql_columns + str(np_arr[i]) + sql_2
        else:
            sql_columns = sql_columns + str(np_arr[i]) + sql_2 + ', '
    logging.debug(sql_columns+' sql columns')

    # extract column and convert to list of single-value tuples
    sql_final = sql + sql_columns + sql_3
    logging.debug(sql_final)
    logging.debug(data_list)
    crsr.executemany(sql_final, data_list)  # insert the query with list of data to db
    connection.commit()

def conver_right_formt_of_tbl_name(option):
    temporar = str(option)
    logging.debug(temporar)
    b = temporar.replace(' ', '_')  # 1.1 replace char to set right format of db table name
   #var_db = ''.join([i for i in b if i or i == '_'])  # 1.2 replace char to set right format of db table name
    #logging.debug(var_db)
    return b

def checkIfDuplicates(listOfElems,x):
    ''' Check if given list contains any duplicates '''
    setOfElems = set(x)
    for elem in listOfElems:
        if elem in setOfElems:
            return True
        else:
            setOfElems.add(elem)
    return False

def upload_data_to_db(v,p,k, list_import_df,list_import_dim, f, np_array):
    v_p_k = np.column_stack((v, p, k))  # set 3 list to one to save to compare it and save needed data to model
    logging.debug('v_p_k')
    logging.debug(v_p_k)
    logging.debug('np_array')
    logging.debug(np_array)

    for i in range(len(v_p_k)):
        if v_p_k[i, 2] == '-none-':  # if none do nothing
            logging.debug('Empty Select field')
        if v_p_k[i, 2] in list_default_dim:  # if item in dim list add it to lists
            list_import_df.append(v_p_k[i, 1])
            list_import_dim.append(v_p_k[i, 2])
        if v_p_k[i, 2] not in list_default_dim and v_p_k[i, 2] in list_custom_dim and v_p_k[i, 2] != '-none-':
            list_import_df.append(v_p_k[i, 1])
            list_import_dim.append(v_p_k[i, 2])
        #if v_p_k[i, 2] not in list_default_dim and v_p_k[i, 2] not in list_custom_dim and v_p_k[i, 2] != '-none-':
            #result = np.where(np_array == v_p_k[i, 2])  # find index of item
            #list_import_df.append(v_p_k[i, 1])  #
            #list_import_dim.append(np_array.item(int(result[0]), int(
                #result[1] - 1)))  # add item to list of dim with cordinates from result
    logging.debug('list_import_df')
    logging.debug(list_import_df)
    logging.debug('list_import_dim')
    logging.debug(list_import_dim)
    # the point is to open the imported file in the end of logik to save time for posible mistake by chosing relations
    file = default_storage.open(f)  # opening the uploaded file
    table_name = 'imported_data'
    df = pd.read_excel(file, "Sheet1", header=0)
    # need to add progress bar
    data = df[
        df.columns.intersection(list_import_df)]  # get from dataFrame only needed columns from post request
    data_list = data.values.tolist()  # convert df to values list
    return list_import_dim, data_list

def exequte_sql(sql_string_header,list_var):
    cursor = connection.cursor()
    cursor.execute(sql_string_header)
    sql_columns_header = cursor.fetchall()
    list_header = np.array(sql_columns_header)
    logging.debug('-------------')
    logging.debug(list_header)
    for i in range(list_header.__len__()):
        logging.debug(list_header.item(i))
        if (list_header.item(i) != 'id'):
            list_var.append(list_header.item(i))
    logging.debug('----------')
    logging.debug(list_var)
    return list_var

def mapping_rules_select(option,dimension_select,list_var):
    if option is not None:
        temporar = str(option)
        logging.debug(option)
    elif dimension_select is not '':
        temporar = str(dimension_select)
        logging.debug(dimension_select)
    b = temporar.replace(' ', '_')  # 1.1 replace char to set right format of db table name
    logging.debug(b)
    var_db = ''.join(
        [i for i in b if i.isalpha() or i == '_'])  # 1.2 replace char to set right format of db table name
    logging.debug(var_db)
    var_template = ''.join(
        [i for i in temporar if
         i or i == ' '])  # replace to set right format for dim. name in template
    cursor = connection.cursor()
    # SQL code to return columns from table
    sql_string = '''select * from engine_app_''' + b.lower()
    print(sql_string)
    sql_string_header = '''select column_name from information_schema.columns where table_name='engine_app_''' + b.lower() + '''' '''
    cursor.execute(sql_string)
    sql_columns = cursor.fetchall()
    cursor.execute(sql_string)
    list_np = np.array(sql_columns)

    if (len(list_np) > 0):
        list_np = np.delete(list_np, [0], axis=1)
        logging.debug(list_np)
    cursor.execute(sql_string_header)
    sql_columns_header = cursor.fetchall()
    list_header = np.array(sql_columns_header)
    logging.debug('-------------')
    logging.debug(list_header)
    for i in range(list_header.__len__()):
        logging.debug(list_header.item(i))
        if (list_header.item(i) == 'code'):
            list_var.append(list_header.item(i))
    logging.debug('----------')
    logging.debug(list_var)
    data = {'var_template': option,
            'list_var': list_var}
    return data

def mapping_rule_select_mt(option_m,mapping_select,dimension_select,list_var_2):
    if option_m is not '':
        var_mepping_t = str(option_m).replace(' ', '_')
    elif mapping_select is not '':
        var_mepping_t = str(mapping_select).replace(' ', '_')
        logging.debug(var_mepping_t)
    cursor = connection.cursor()
    logging.debug(str(option_m) + '-----------')
    var_dimension = str(dimension_select).replace(' ', '_')
    logging.debug(var_dimension)
    # SQL code to return columns from table
    sql_string_2 = '''select * from engine_app_''' + var_mepping_t.lower()
    sql_string_header_2 = '''select column_name from information_schema.columns where table_name='engine_app_''' + var_mepping_t.lower() + '''' '''
    cursor.execute(sql_string_2)
    sql_columns = cursor.fetchall()
    list_np = np.array(sql_columns)
    if (len(list_np) > 0):
        list_np = np.delete(list_np, [0], axis=1)
        logging.debug(list_np)
    cursor.execute(sql_string_header_2)
    sql_columns_header_2 = cursor.fetchall()
    list_header_2 = np.array(sql_columns_header_2)
    logging.debug('-------------')
    logging.debug(list_header_2)
    for i in range(list_header_2.__len__()):
        logging.debug(list_header_2.item(i))
        if (list_header_2.item(i) != 'id'):
            list_var_2.append(list_header_2.item(i))
    obj = Mapping_Data.objects.get(name=option_m)#change to
    return {'mapping_t': option_m,
                    'list_var_2': list_var_2}
logging.debug('End of Program')