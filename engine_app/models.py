from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Dimensions(models.Model):
    dimensionName = models.CharField(max_length=255)
    new_name = models.CharField(max_length=100, default=None, null=True)
    class Meta:
        ordering = ['id']

class Mapping_Table(models.Model):
    mtName = models.CharField(max_length=255)

class Mapping_Sets(models.Model):
    setName = models.CharField(max_length=255)

class Mapping_Data(models.Model):
    name = models.CharField(max_length=100)
    new_name = models.CharField(max_length=100, default=None, null=True)

    class Meta:
        ordering = ['id']

class Mapping_Rules_Main(models.Model):
    ruleName = models.CharField(max_length=255)

class Mapping_Rules(models.Model):
    ruleName = models.ForeignKey(Mapping_Rules_Main, on_delete=models.DO_NOTHING)
    type = models.CharField(max_length=255,default=None,null=True)
    row = models.CharField(max_length=255,default=None,null=True)
    dimensionName = models.ForeignKey(Dimensions, on_delete=models.DO_NOTHING, blank=True, null=True)
    dimField = models.CharField(max_length=255,default=None,null=True)
    mtName = models.ForeignKey(Mapping_Data, on_delete=models.DO_NOTHING)
    mtField = models.CharField(max_length=255,default=None,null=True)
    #setName = models.ForeignKey(Mapping_Sets, on_delete=models.SET_NULL,null=True)
    setName = models.ManyToManyField(Mapping_Sets)

class Log_Reporting(models.Model):
    event     = models.CharField(max_length=255, default=None,null=True)
    period    = models.CharField(max_length=255, default=None,null=True)
    file      = models.CharField(max_length=255, default=None,null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user    = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    comment = models.CharField(max_length=255, default=None,null=True)

class Log_Mapping_Performe(models.Model):
    event = models.CharField(max_length=255)
    period = models.CharField(max_length=7)
    setName = models.ForeignKey(Mapping_Sets, on_delete=models.DO_NOTHING)
    timestampImportD = models.DateTimeField(auto_now_add=True)
    lastRun = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)

class Imported_Data(models.Model):
    reporting_event = models.CharField(max_length=255, default=None, null=True)
    reporting_period = models.CharField(max_length=255, default=None, null=True)
    entity  = models.CharField(max_length=255, default=None, null=True)
    konto = models.CharField(max_length=255, default=None, null=True)
    partner = models.CharField(max_length=255, default=None, null=True)
    movement_type = models.CharField(max_length=255, default=None, null=True)
    investe = models.CharField(max_length=255, default=None, null=True)
    document_type = models.CharField(max_length=255, default=None, null=True)
    value_in_lc = models.CharField(max_length=255, default=None, null=True)
    value_in_gc = models.CharField(max_length=255, default=None, null=True)
    value_in_tc = models.CharField(max_length=255, default=None, null=True)
    quantity = models.CharField(max_length=255, default=None, null=True)

class Output_Data(models.Model):
    reporting_event = models.CharField(max_length=255, default=None, null=True)
    reporting_period = models.CharField(max_length=255, default=None, null=True)
    entity  = models.CharField(max_length=255, default=None, null=True)
    konto = models.CharField(max_length=255, default=None, null=True)
    partner = models.CharField(max_length=255, default=None, null=True)
    movement_type = models.CharField(max_length=255, default=None, null=True)
    investe = models.CharField(max_length=255, default=None, null=True)
    document_type = models.CharField(max_length=255, default=None, null=True)
    custom_1 = models.CharField(max_length=255, default=None, null=True)
    custom_2 = models.CharField(max_length=255, default=None, null=True)
    custom_3 = models.CharField(max_length=255, default=None, null=True)
    custom_4 = models.CharField(max_length=255, default=None, null=True)
    value_in_lc = models.CharField(max_length=255, default=None, null=True)
    value_in_gc = models.CharField(max_length=255, default=None, null=True)
    value_in_tc = models.CharField(max_length=255, default=None, null=True)
    quantity = models.CharField(max_length=255, default=None, null=True)

class Betrag(models.Model):
    name = models.CharField(max_length=255, default=None, null=True)

class Dimensions_Abstract(models.Model):
    code = models.CharField(max_length=4, default=None, null=True)
    long_descr = models.CharField(max_length=30, default=None, null=True)
    short_descr = models.CharField(max_length=120, default=None, null=True)

    class Meta:
        abstract = True
class Master_Data(models.Model):
    name = models.CharField(max_length=100)



class Reporting_Event(Dimensions_Abstract):
    pass
class Reporting_Period(Dimensions_Abstract):
    pass
class Entity(Dimensions_Abstract):
    pass
class Konto(Dimensions_Abstract):
    pass
class Partner(Dimensions_Abstract):
    pass
class Movement_Type(Dimensions_Abstract):
    pass
class Investe(Dimensions_Abstract):
    pass
class Document_Type(Dimensions_Abstract):
    pass
class Custom_1(Dimensions_Abstract):
    pass
class Custom_2(Dimensions_Abstract):
    pass
class Custom_3(Dimensions_Abstract):
    pass
class Custom_4(Dimensions_Abstract):
    pass

class mapping_table(models.Model):
    class Meta:
        abstract = True

class mapping_t_1(mapping_table):
    pass
class mapping_t_2(mapping_table):
    pass
class mapping_t_3(mapping_table):
    pass
class mapping_t_4(mapping_table):
    pass
class mapping_t_5(mapping_table):
    pass
class mapping_t_6(mapping_table):
    pass
class mapping_t_7(mapping_table):
    pass
class mapping_t_8(mapping_table):
    pass
class mapping_t_9(mapping_table):
    pass
class mapping_t_10(mapping_table):
    pass