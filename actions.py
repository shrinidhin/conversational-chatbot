from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from spell_corrector import rectify

from rasa_core.actions.action import Action
from rasa_core.events import SlotSet
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import zomatopy
import json

class ActionSearchRestaurants(Action):
	def name(self):
		return 'action_restaurant'
	
	def run(self, dispatcher, tracker, domain):

		# Reading budget value provided by user
		UserBudget = tracker.get_slot('budget')
		
		# Reading location provided by user
		#loc = tracker.get_slot('location')
		user_location =	rectify(tracker.get_slot('location'))
		loc = user_location
		
		# Reading cuisine provided by user
		cuisine = tracker.get_slot('cuisine')

		CityFile = open("CityFile.txt")
		CityData = CityFile.read()
		CityList = CityData.split()
		MatchCity = [City for City in CityList if str(loc).lower() == City.lower()]
		if len(MatchCity) == 0:
			dispatcher.utter_message("Sorry, But Currntly we don't provide service in requested city.")
			return [SlotSet('location',loc)]
			
		if tracker.get_slot('location').lower() != user_location:
			dispatcher.utter_message("\n Did you mean : " + user_location + "\n\n" + search_restaurants(UserBudget, cuisine, loc, 5))
		else:
			dispatcher.utter_message(search_restaurants(UserBudget, cuisine, loc, 5))
		
		return [SlotSet('location',loc)]
		
class ActionSendEmail(Action):
	def name(self):
		return 'action_sendemail'
	
	def run(self, dispatcher, tracker, domain):
		# Reading Email address provided by user
		EmailAddress = tracker.get_slot('email_address')
		
		# Reading budget value provided by user
		UserBudget = tracker.get_slot('budget')
		
		# Reading location provided by user
		# loc = tracker.get_slot('location')
		user_location =	rectify(tracker.get_slot('location'))
		loc = user_location
		
		# Reading cuisine provided by user
		cuisine = tracker.get_slot('cuisine')
			
		# msg = EmailMessage()
		msg = MIMEMultipart()

		me = 'restaurantchatbot.upgrad@gmail.com'
		password = 'upgradchatbot'
		you = EmailAddress
		msg['Subject'] = 'Restaurant Chatbot'
		msg['From'] = me
		msg['To'] = you

		body = search_restaurants(UserBudget, cuisine, loc, 10)
		
		# Record the MIME types of both parts - text/plain and text/html.
		part1 = MIMEText(body, 'plain')
		part2 = MIMEText(body, 'html')
		
		msg.attach(part1)
		#msg.attach(part2)

		# Send the message via our own SMTP server.
		s = smtplib.SMTP("smtp.gmail.com", 587)
		s.starttls()
		s.login(me, password)
		s.sendmail(msg['From'], msg['To'], msg.as_string())
		s.quit()
			
def search_restaurants(UserBudget, cuisine, loc, number_of_records):
	UserBudget = str(UserBudget)
	if not UserBudget:
		UserBudget = "700"	# Default user budget
	BudgetList = UserBudget.split("-")

	config={ "user_key":"02af854c9a6a6d8acbbb7fb36b938fef"}
	zomato = zomatopy.initialize_app(config)
	
	location_detail=zomato.get_location(loc, 1)
	d1 = json.loads(location_detail)
	lat=d1["location_suggestions"][0]["latitude"]
	lon=d1["location_suggestions"][0]["longitude"]
	cuisines_dict={'bakery':5,'chinese':25,'cafe':30,'italian':55,'biryani':7,'north indian':50,'south indian':85}
	results=zomato.restaurant_search("", lat, lon, str(cuisines_dict.get(cuisine)), number_of_records)
	d = json.loads(results)
	response=""
	
	if d['results_found'] == 0:
		response= "no results"
	else:
		# Creating a List of Restuarnats with its average user rating value
		RestaurantDict = {}
		RestaurantCount = 0
		for restaurant in d['restaurants']:
			RestaurantDict[str(restaurant['restaurant']['name'])] = float(restaurant['restaurant']['user_rating']['aggregate_rating'])

		# Sorting restaurants as per user rating in descending order
		SortedList = sorted(RestaurantDict.items(), key=lambda x: x[1],reverse=True)
		for RestaurantName in SortedList:
			restaurant = [restaurant for restaurant in d['restaurants'] if str(restaurant['restaurant']['name']).lower() == str(RestaurantName[0]).lower()]
			restaurant = restaurant[0]

			# Reading restaurant's avg budget for two peopel
			RestaurantBudget = int(restaurant['restaurant']['average_cost_for_two'])
				
			# Filetring restaurants to match user's budget criteria
			if len(BudgetList) == 2:
				if (int(RestaurantBudget) >= int(BudgetList[0])) and (int(RestaurantBudget) <= int(BudgetList[1])):
					RestaurantCount += 1
					response=response+ str(RestaurantCount) + ". " + restaurant['restaurant']['name']+ " in "+ restaurant['restaurant']['location']['address']+ " has been rated : "  + restaurant['restaurant']['user_rating']['aggregate_rating']+ " with Average Cost for two people: " + str(restaurant['restaurant']['average_cost_for_two']) + "\n"
			else:
				if int(BudgetList[0]) == 300:
					if (int(RestaurantBudget) <= 300):
						RestaurantCount += 1
						response=response+ str(RestaurantCount) + ". " + restaurant['restaurant']['name']+ " in "+ restaurant['restaurant']['location']['address']+ " has been rated : "  + restaurant['restaurant']['user_rating']['aggregate_rating']+ " with Average Cost for two people: " + str(restaurant['restaurant']['average_cost_for_two']) + "\n"
				elif int(BudgetList[0]) == 700:
					if (int(RestaurantBudget) >= 700):
						RestaurantCount += 1
						response=response+ str(RestaurantCount) + ". " + restaurant['restaurant']['name']+ " in "+ restaurant['restaurant']['location']['address']+ " has been rated : "  + restaurant['restaurant']['user_rating']['aggregate_rating']+ " with Average Cost for two people: " + str(restaurant['restaurant']['average_cost_for_two']) + "\n"

	if not response:
		response = "We are unable to find restaurant which match your requirements"
	
	return response
	
