import random


def initiateOCCUPANCY(otas, properties):
    occupancy = {}
    for ota in otas:
        occupancy[ota] = {}
        for property in properties:
            occupancy[ota][property] = []

    return occupancy


def getAvailableProperties(ota, occupancy, dates):
    available_properties = []
    for property in occupancy[ota]:
        if len(list(set(occupancy[ota][property]) & set(dates))) == 0:
            available_properties.append(property)
    return available_properties


def getAnotherOTA(ota):
    if ota == "A":
        return "B"
    return "A"


def isOverbooking(ota, occupancy, property, dates):
    anotherOTA = getAnotherOTA(ota)
    if len(list(set(occupancy[anotherOTA][property]) & set(dates))) > 0:
        return True
    return False


def makeBooking(ota, property, occupancy, day_checkin, day_checkout):
    occupancy[ota][property] = list(set(occupancy[ota][property]) | set(range(day_checkin, day_checkout)))
    return occupancy


def generateRandomDemand(OTAS):
    ota = OTAS[random.randint(0, len(OTAS) - 1)];
    day_checkin = random.randint(1, 14)
    day_checkout = random.randint(day_checkin + 1, day_checkin + 4)

    return (ota, day_checkin, day_checkout)


def generateBookings(OCCUPANCY, OTAS, number_of_bookings=1000):
    BOOKINGS = []
    for i in range(1, number_of_bookings + 1):
        (ota, day_checkin, day_checkout) = generateRandomDemand(OTAS)
        available_properties = getAvailableProperties(ota, OCCUPANCY, range(day_checkin, day_checkout))
        print(i)
        if len(available_properties) > 0:
            property = available_properties[random.randint(0, len(available_properties) - 1)]
            if isOverbooking(ota, OCCUPANCY, property, range(day_checkin, day_checkout)):
                status = "overbooking"
            else:
                OCCUPANCY = makeBooking(ota, property, OCCUPANCY, day_checkin, day_checkout)
                status = "ok"
        else:
            status = "no availability"

        booking = {
            "booking": i,
            "ota": ota,
            "property": property,
            "date_checkin": "2018-12-%02d" % (day_checkin,),
            "date_checkout": "2018-12-%02d" % (day_checkout,),
            "status": status
        }
        BOOKINGS.append(booking)
        print(booking)
    return BOOKINGS
