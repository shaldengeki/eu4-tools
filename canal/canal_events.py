#!/usr/bin/env python
import calendar
import datetime
import decimal
import numpy
import random

class Run(object):
  def __init__(self, rule, province=None, climate=None, religion=None, start_date=None, curr_date=None, money=0, unrest=0, rebels=0, manpower=0, adm=0, dip=0, mil=0, check_event_every_days=20):
    # function that takes a set of choices and outputs the choice to make.
    self.rule = rule

    # name of province that canal is being built in, e.g. 'panama'
    self.province = str(province)

    # list of climates in the province, e.g. ['arid']
    if climate is None:
      climate = []
    self.climate = climate

    # default to eu4 start date.
    if start_date is None:
      start_date = datetime.date(year=1444, month=11, day=11)
    self.start_date = start_date

    # canals take 10 years to build.
    self.finish_date = datetime.date(year=self.start_date.year + 10, month=self.start_date.month, day=self.start_date.day)

    if curr_date is None:
      curr_date = self.start_date
    self.curr_date = curr_date

    self.days = (self.curr_date - self.start_date).days
    self.total_days = (self.finish_date - self.start_date).days
    self.days_left = self.total_days - self.days

    self.money = decimal.Decimal(money)
    self.unrest = int(unrest)
    self.rebels = int(rebels)
    self.manpower = int(manpower)

    # religion group in province, e.g. 'christian' or 'muslim'
    if religion is None:
      religion = 'christian'
    self.religion = religion
    self.adm = int(adm)
    self.dip = int(dip)
    self.mil = int(mil)

    self.check_event_every_days = int(check_event_every_days)
  def current_month_days(self):
    return calendar.monthrange(self.curr_date.year, self.curr_date.month)[1]
  def run(self, events):
    while self.days_left > 0:
      # check events.
      for event in events:
        if event.can_fire(self) and event.does_fire(self):
          # print event.__class__.__name__
          event.fire(self)
      # jump ahead to the next event check.
      self.days_left -= self.check_event_every_days
      try:
        if self.days_left < 0:
          # we've reached the end. rewind to the exact end date.
          orig_days_left = int(self.days_left + self.check_event_every_days)
          self.days += orig_days_left
          self.curr_date += datetime.timedelta(days=orig_days_left)
          self.days_left = 0
        else:
          self.days += self.check_event_every_days
          self.curr_date += datetime.timedelta(days=self.check_event_every_days)
      except OverflowError:
        print "Indefinite run, halting."
        break

class Choice(object):
  def __str__(self):
    return " ".join([
      "<Choice",
      str(self.adm),
      "ADM",
      str(self.dip),
      "DIP",
      str(self.mil),
      "MIL",
      str(self.unrest),
      "Unr.",
      str(self.rebels),
      "Rebs",
      str(self.manpower),
      "Men",
      str(self.income),
      "Income",
      str(self.progress),
      "Prog.",
      ">"
    ])
  def __init__(self, adm=0, dip=0, mil=0, unrest=0, rebels=0, manpower=0, income='0.00', progress='0.00', flags=None):
    self.adm = int(adm)
    self.dip = int(dip)
    self.mil = int(mil)
    self.monarch_points = self.adm + self.dip + self.mil

    self.unrest = int(unrest)
    self.rebels = int(rebels)
    self.manpower = int(manpower)
    self.income = decimal.Decimal(income)
    self.progress = decimal.Decimal(progress)
    self.flags = flags
  def pick_choice(self, run):
    # set any flags this choice explicitly sets.
    if self.flags is not None:
      for flag in self.flags:
        setattr(eval(flag[0]), flag[1], flag[2])
    # change run's attributes by this choice.
    run.money += self.income
    run.unrest = self.unrest
    run.rebels += self.rebels
    run.manpower += self.manpower
    run.adm += self.adm
    run.dip += self.dip
    run.mil += self.mil
    # the impact of progress is proportional to the total number of construction days.
    # this means that as you extend the construction longer, further setbacks get worse and worse
    run.days_left -= run.total_days * self.progress
    run.total_days = run.days + run.days_left
    return

class CanalEvent(object):
  mtth = 0
  choices = []
  min_days = 0
  dependencies = []
  has_fired = False
  def mean_time_to_happen(self, run):
    if isinstance(self.__class__.mtth, int):
      return self.__class__.mtth
    else:
      return self.__class__.mtth(run)
  def chance_of_happening(self, run):
    return (1 - pow(2, -1.0 * run.check_event_every_days / (self.mean_time_to_happen(run)*run.current_month_days())))
  def does_fire(self, run):
    return random.random() < self.chance_of_happening(run)
  def can_fire(self, run):
    return run.days >= self.__class__.min_days and all(x.has_fired for x in self.__class__.dependencies)
  def fire(self, run):
    self.__class__.has_fired = True
    choice = run.rule(self.__class__.choices)
    # print "Picked: " + str(choice)
    # print ""
    choice.pick_choice(run)
    self.after_fire(run)
  def after_fire(self, run):
    pass

# Generic events
class AdmProgressBadEvent(CanalEvent):
  mtth = 84
  choices = [Choice(adm=-100), Choice(progress='-0.05')]

class DipProgressBadEvent(CanalEvent):
  mtth = 84
  choices = [Choice(dip=-100), Choice(progress='-0.05')]

class UnrestProgressBadEvent(CanalEvent):
  mtth = 84
  choices = [Choice(unrest=10), Choice(progress='-0.05')]

class AridTropicalLongerEvent(CanalEvent):
  mtth = staticmethod(lambda r: 84 * (1.5 if 'tropical' in r.climate else 1) * (1.25 if 'arid' in r.climate else 1))

# Actual events
class AlcoholRations(CanalEvent):
  mtth = 84
  choices = [Choice(progress='0.025', income='-0.5'), Choice(progress='-0.05')]
  def can_fire(self, run):
    return run.religion != 'muslim' and super(AlcoholRations, self).can_fire(run)

class PoorPlanning(AdmProgressBadEvent):
  pass

class WeakLeadership(AdmProgressBadEvent):
  pass

class NewLeadership(AdmProgressBadEvent):
  pass

class DisatrousLandslide(AdmProgressBadEvent):
  pass

class DwindlingLocalTrade(DipProgressBadEvent):
  pass

class LackOfProvision(DipProgressBadEvent):
  pass

class SevereFloods(DipProgressBadEvent):
  pass

class IncreasedDrunkenness(UnrestProgressBadEvent):
  dependencies = [AlcoholRations]
  choices = [Choice(unrest=10, flags=[("AlcoholRations", "has_fired", False)]), Choice(progress='-0.05')]

class CanalCompanyScheme(AridTropicalLongerEvent):
  min_days = 1825
  choices = [Choice(unrest=10, rebels=2, flags=[("CanalCompanyScheme", "has_fired", True)]), Choice(progress='-0.05', income='-1.0', flags=[("CanalCompanyScheme", "has_fired", True)])]
  def can_fire(self, run):
    return not self.__class__.has_fired and super(CanalCompanyScheme, self).can_fire(run)

class GoodLeadership(AridTropicalLongerEvent):
  choices = [Choice(progress='0.025')]

class GoodWeather(AridTropicalLongerEvent):
  choices = [Choice(progress='0.025')]

class CanalCompanyFormed(CanalEvent):
  mtth = 84
  choices = [Choice(progress='0.025')]
  def can_fire(self, run):
    return not self.__class__.has_fired and super(CanalCompanyFormed, self).can_fire(run)

class OutbreakOfIllness(CanalEvent):
  mtth = staticmethod(lambda r: 84 * (0.75 if 'tropical' in r.climate else 1))
  choices = [Choice(manpower=-10000), Choice(progress='-0.05')]
  def can_fire(self, run):
    return run.manpower >= 12000 and ('tropical' in run.climate or 'arid' in r.climate) and super(OutbreakOfIllness, self).can_fire(run)

class OutbreakOfIllness2(CanalEvent):
  mtth = staticmethod(lambda r: 84 * (0.75 if 'tropical' in r.climate else 1))
  choices = [Choice(manpower=-10000), Choice(progress='-0.05')]
  def can_fire(self, run):
    return run.manpower >= 12000 and ('tropical' in run.climate or 'arid' in r.climate) and super(OutbreakOfIllness2, self).can_fire(run)

class ViolentThunderstorms(DipProgressBadEvent):
  def can_fire(self, run):
    return 'tropical' in run.climate and super(ViolentThunderstorms, self).can_fire(run)

class CanalCrossingRiver(CanalEvent):
  mtth = 84
  choices = [Choice(adm=-100), Choice(manpower=-10000)]
  def can_fire(self, run):
    return run.province == 'panama' and run.manpower >= 12000 and super(CanalCrossingRiver, self).can_fire(run)

class LackOfFreshWater(DipProgressBadEvent):
  mtth = 84
  def can_fire(self, run):
    return ('tropical' in run.climate or 'arid' in run.climate) and super(LackOfFreshWater, self).can_fire(run)

# list of events, for easy reference.
events = [AlcoholRations(),PoorPlanning(),WeakLeadership(),NewLeadership(),DisatrousLandslide(),DwindlingLocalTrade(),LackOfProvision(),SevereFloods(),IncreasedDrunkenness(),CanalCompanyScheme(),GoodLeadership(),GoodWeather(),CanalCompanyFormed(),OutbreakOfIllness(),OutbreakOfIllness2(),ViolentThunderstorms(),CanalCrossingRiver(),LackOfFreshWater()]

# some basic rules.
def maximize_monarch_points(choices):
  return max(choices, key=lambda c: c.monarch_points)

def maximize_money(choices):
  return max(choices, key=lambda c: c.income)

def maximize_progress(choices):
  return max(choices, key=lambda c: c.progress)

def reset_events(events):
  for e in events:
    e.__class__.has_fired = False

def perform_runs(rule, n=1000):
  progress_step = n/10
  runs = []
  for i in xrange(n):
    run = Run(rule)
    run.run(events)
    runs.append(run)
    reset_events(events)
    if i % progress_step == 0:
      print "Progress:",round(100.0*i/n, 2),"%"
  return runs

def runs_stats(runs):
  days = []
  money = []
  unrest = []
  rebels = []
  manpower = []
  adm = []
  dip = []
  mil = []
  for r in runs:
    days.append(r.days)
    money.append(round(r.money, 2))
    unrest.append(r.unrest)
    rebels.append(r.rebels)
    manpower.append(r.manpower)
    adm.append(r.adm)
    dip.append(r.dip)
    mil.append(r.mil)
  row_format = "{:>8}{:>15}{:>15}{:>15}{:>15}"
  print row_format.format("Stat", "Min", "Max", "Mean", "Median")
  print "===================================================================="
  print row_format.format("Days:", min(days), max(days), numpy.mean(days), numpy.median(days))
  print row_format.format("Money:", min(money), max(money), numpy.mean(money), numpy.median(money))
  print row_format.format("Unrest:", min(unrest), max(unrest), numpy.mean(unrest), numpy.median(unrest))
  print row_format.format("Rebs:", min(rebels), max(rebels), numpy.mean(rebels), numpy.median(rebels))
  print row_format.format("Men:", min(manpower), max(manpower), numpy.mean(manpower), numpy.median(manpower))
  print row_format.format("ADM:", min(adm), max(adm), numpy.mean(adm), numpy.median(adm))
  print row_format.format("DIP:", min(dip), max(dip), numpy.mean(dip), numpy.median(dip))
  print row_format.format("MIL:", min(mil), max(mil), numpy.mean(mil), numpy.median(mil))
