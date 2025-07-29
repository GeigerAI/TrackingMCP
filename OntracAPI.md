![background image](OnTrac Web Service Integration Specifications001.png)

1

Web Service Integration Specifications

TABLE OF CONTENTS

Introduction \& Overview ............................................................................................................................................... 3

Terms Of Use ................................................................................................................................................................. 4

Contact Information ...................................................................................................................................................... 4

Access ............................................................................................................................................................................ 4

API Updates ................................................................................................................................................................... 5

Zips................................................................................................................................................................................. 5

Location ......................................................................................................................................................................... 5

Available Methods ......................................................................................................................................................... 5

GET ................................................................................................................................................................................. 5

Examples ........................................................................................................................................................................ 6

Shipments ...................................................................................................................................................................... 7

Location ......................................................................................................................................................................... 7

Available Methods ......................................................................................................................................................... 7

POST............................................................................................................................................................................... 7

Examples ........................................................................................................................................................................ 9

GET ............................................................................................................................................................................... 11

Examples ...................................................................................................................................................................... 13

Shipment Errors ........................................................................................................................................................... 14

Rates ............................................................................................................................................................................ 15

Location ....................................................................................................................................................................... 15

Available Methods ....................................................................................................................................................... 15

GET ............................................................................................................................................................................... 15

![background image](OnTrac Web Service Integration Specifications002.png)

Web Service Integration Specifications

2

OnTrac Shipping Label Formation ............................................................................................................................... 19

OnTrac Shipping Label Diagram ................................................................................................................................... 20

Sample Labels .............................................................................................................................................................. 22

OnTrac Shipping Label PDF-417 Symbol Specifications ............................................................................................... 23

OnTrac Data Stream Format for ANSI MH10.8.3 Compliance ..................................................................................... 23

Non-Printable ASCII Characters Used in Data Stream ................................................................................................. 24

ANSI MH10.8.3 Data Stream Example ......................................................................................................................... 25

OnTrac Shipping Label Code 128-C Routing Symbol Specifications............................................................................. 26

OnTrac Shipping Label Code 128-B Tracking Number Symbol Specifications ............................................................. 26

OnTrac Tracking Number ............................................................................................................................................. 26

Check Digit Calculation ................................................................................................................................................ 27

Check Digit Example 1 ................................................................................................................................................. 27

Check Digit Example 2 ................................................................................................................................................. 27

Check Digit Example 3 ................................................................................................................................................. 27

OnTrac Status Codes .................................................................................................................................................... 28

![background image](OnTrac Web Service Integration Specifications003.png)

Web Service Integration Specifications

3

INTRODUCTION \& OVERVIEW

The OnTrac Web Service interface is designed using the REST approach. In order to interact with the OnTrac   
system the user must first identify the proper resource they need and then pick the proper HTTP method to use.   
OnTrac currently has four exposed resources: shipments, zips, rates, and pickup. Using the HTTP methods GET and   
POST along with these resources will allow the user to fully interface with the OnTrac system.

By transmitting API shipment data and producing integrated labels, the account holder agrees to OnTrac's Terms   
and Conditions of Carriage; see

ontrac.com

for more information.

A set of XSDs will be included in this document that describes the format of requests and responses for interacting   
with OnTrac. Please note that the response structures are subject to change and the XSD should be used as a   
development guide only to prevent unwanted failures due to these changes.

For example, if a user would like to rate a package, they must use an HTTP GET on the rates resource to receive a   
quote. If the user then decides to ship the package, they must create a shipment. To create a shipment, the user   
would perform an HTTP POST to the shipments resource. To track the progress of the package, the user may then   
perform an HTTP GET on the shipments resource. In a similar manner, all necessary functions required for   
integration can be performed.

Below is a list of the existing resources, the methods you may perform on them and a brief description of the   
action.

Shipments



GET -- Track a package or get package detail updates



POST -- Create a new shipment in the OnTrac system



There is no method to delete a shipment in the OnTrac system. All packages are considered inactive until   
the tracking number is physically scanned. If a package is never scanned, the customer will not be   
charged.

Rates



GET -- Requests rate quotes for one or more packages

ZIPs



GET -- Request a detailed list of ZIPs serviced by OnTrac

![background image](OnTrac Web Service Integration Specifications004.png)

Web Service Integration Specifications

4

TERMS OF USE

Active OnTrac account holders may use our API to successfully rate, ship and track OnTrac shipments. Users are   
not to exceed a reasonable amount of API calls, as outlined below. API use is for OnTrac customers only.   
Customers are not to disclose their API credentials to anyone, including third-party auditors or shipment tracking   
services. When developing on our platform you agree to all of the terms listed below:

Application Restrictions

Tracking --

1.

Only packages tendered to OnTrac should be tracked. Do not track packages for other carriers such as   
UPS, FedEx or DHL.

2.

Shipments should not be tracked prior to being tendered to OnTrac.

3.

Once delivered, shipments should not be tracked again.

4.

Tracking shipments several times a day is acceptable, but limited to 5 calls per package per day.

5.

Tracking is limited to 500 calls per minute. Exceeding this limit could cause errors and latency.

6.

Shipments older than two weeks, regardless of status, should not be tracked.

7.

Special requests for shipments older than two weeks should be sent via email to

ont@ontrac.com

Users in violation of Terms of Use will be contacted by OnTrac and will be expected to take immediate action to   
rectify outlined issues. If full compliance is not demonstrated, OnTrac may restrict or terminate access to our API   
services.

CONTACT INFORMATION

To activate an OnTrac API password and technical support please contact:

ont@ontrac.com

ACCESS

For testing purposes, use your issued account number and API password. To request a password, contact   
ont@ontrac.com. Please include the account number in the email. Once ready to send test shipments or get rates,   
make calls to our production server.

The root URL of the TEST site is:   

https://www.shipontrac.net/OnTracTestWebServices/OnTracServices.svc

The root URL of the PRODUCTION site is:   

https://www.shipontrac.net/OnTracWebServices/OnTracServices.svc

\*Note -- Any packages transmitted to the test server will not be trackable on the production server and vice versa.   
Also, any rates that are requested from the test server may not be accurate.

![background image](OnTrac Web Service Integration Specifications005.png)

Web Service Integration Specifications

5

API UPDATES

Scheduled updates to the OnTrac Web Services will occur on a quarterly basis, when required. Any requested   
changes will be held until the next scheduled maintenance period. Updates will be published to the test server   
approximately 30 days prior to going live and all API customers will be notified of the details of the new changes.   
This is to allow all users time to incorporate the new features and to verify their existing code is functioning   
properly.

All quarterly API changes will be backwards compatible. Any issues encountered with legacy code should be   
communicated to OnTrac immediately so that we may address any concerns and delay the move to production, if   
necessary. If OnTrac has not received any requests for delay after the 30-day testing period, the changes will be   
published to the production server on the following Monday. These quarterly updates will be fully backwards   
compatible and will not require customer integration changes. Any changes that require alteration of the   
customer's API integration will only be implemented with a six month notice and full testing opportunities during   
that period.

There may be times when an out-of-cycle update is required, based on business needs. If this occurs, all API   
customers will be notified and a shortened testing period will be provided. Specific details will be provided at the   
time. All efforts will be made to avoid unscheduled changes and to minimize customer impact when such a change   
is required.

ZIPS

LOCATION

PRODUCTION   

https://www.shipontrac.net/OnTracWebServices/OnTracServices.svc/V7/{account}/Zips   

TEST

https://www.shipontrac.net/OnTracTestWebServices/OnTracServices.svc/V7/{account}/Zips

\*Note -- {account} represents a valid OnTrac user account in the above URLs

AVAILABLE METHODS

GET

The GET method will return a list of serviced OnTrac Zip codes and their relevant service information. The list will   
be returned as an XML document in the body of the HTTP response.

![background image](OnTrac Web Service Integration Specifications006.png)

Web Service Integration Specifications

6

Parameters

Name

Required

Format

pw

Yes

String

lastUpdate

No

String "yyyy-MM-dd"

The "pw" should contain the web password associated with the OnTrac account making the request.

The "lastUpdate" parameter should contain the date of the last Zip request made to the OnTrac system. Only Zips   
that have been added or changed since this date will be returned. If this parameter is not included, all Zips will be   
returned.

Return Structure

The structure of the XML response is described OnTracZipResponse.XSD. Below is a brief description of the XML   
data elements and their formats.

Name

Format

Description

zipCode

String

5 digit USPS Zip

saturdayServiced

Byte

0 - Unavailable   
1 - Available

pickupServiced

Byte

0 - Unavailable   
1 - Available

sortCode

String

3 or 4 character OnTrac sort code

EXAMPLES

Example Request URL

https://www.shipontrac.net/OnTracTestWebServices/OnTracServices.svc/V7/37/Zips?pw=testpass\&lastUpdate=2  
022-10-12

Example XML Response

\<

OnTracZipResponse

xmlns:xsi

="

http://www.w3.org/2001/XMLSchema-instance

"

xmlns:xsd

="

http://www.w3.org/2001/XMLSchema

"\>

\<

Zips

\>

\<

Zip

\>

\<

zipCode

\>

90210

\</

zipCode

\>

\<

saturdayServiced

\>1\</

saturdayServiced

\>

\<

pickupServiced

\>

1

\</

pickupServiced

\>

\<

sortCode

\>

COM

\</

sortCode

\>

\</

Zip

\>

\</

Zips

\>

\<

Error

/\>

\</

OnTracZipResponse

\>  
![background image](OnTrac Web Service Integration Specifications007.png)

Web Service Integration Specifications

7

SHIPMENTS

LOCATION

PRODUCTION   

https://www.shipontrac.net/OnTracWebServices/OnTracServices.svc/V7/{account}/shipments

TEST   

https://www.shipontrac.net/OnTracTestWebServices/OnTracServices.svc/V7/{account}/shipments

\*Note -- {account} represents a valid OnTrac user account in the above URLs

AVAILABLE METHODS

POST

An HTTP POST to this resource with an XML structure as described in OnTracShipmentRequest.XSD will create a   
new shipment in the OnTrac system. The response will contain a XML structure as described in   
OnTracShipmentResponse.XSD. This response will contain shipping costs and all necessary information for   
creating/printing an OnTrac shipping label. Shipment requests are limited to 100 packages per request.

\* Note -- The tracking element in the request is for use if the client is generating tracking numbers locally using a   
seed number from OnTrac. If the tracking element is left blank, the server will assign a tracking number to the   
shipment and it will be returned in the response.

Parameters

Name

Required

Format

pw

Yes

String

The "pw" should contain the API password associated with the OnTrac account making the request.

Request Structure

The structure of the XML request is described OnTracShipmentRequest.xsd. Below is a brief description of the XML   
data elements and their formats. All elements are required in the XML document, but only elements marked as   
required must have a value, e.g. you must include a \<Reference\> element but \<Reference /\> is valid.

Name

Format

Max Length

Required

Description

UID

String

none

No

For customer use only to associate a response to a   
request.

Name

String

30

Yes

Company Name

Addr1

String

Del - 60   
PU - 43

Yes

Delivery Street Address

Addr2

String

60

No

Suite if required  
![background image](OnTrac Web Service Integration Specifications008.png)

Web Service Integration Specifications

8

Addr3

String

60

No

Not currently used

City

String

20

Yes

State

String

Yes

2 character USPS state abbreviation

Zip

String

10

Yes

5 digit Zip code

Contact

String

20

No

Contact Name

Phone

String

13

Yes

Contact Phone

Service

String

2

Yes

C -- Ground

SignatureRequired

Boolean

Yes

Residential

Boolean

Yes

Indicates a residential delivery

SaturdayDel

Boolean

Yes

Indicate Saturday delivery service

Weight

Float

Yes

Package weight in lbs. A zero indicates a letter; all   
other values will be rated as a package

BillTo

Integer

No

Contains a valid OnTrac account number for third   
party billing

Instructions

String

100

No

Special delivery instructions for the driver

Reference

String

50

No

Customer reference number

Reference2

String

50

No

Customer reference number 2

Reference3

String

50

No

Not currently used. This is a space holder for future   
versions and values will be ignored

Tracking

String

15

No

Contains a valid OnTrac tracking number. Tracking   
numbers from previous requests or locally created   
tracking numbers should be placed here

DIM

Float

No

Contains the length, width, and height of the package

LabelType

Integer

No

0 = No label   
1 = PDF label = Half Page, Upper Right Side Justified   
9 = 4 x 6 ZPL label   
12 = PNG label   
13 = PDF Centered Justified 2018

ShipEmail

String

50 per address

No

Semicolon delimited list of email addresses to receive   
a notification from OnTrac when then shipment is   
created

DelEmail

String

50 per address

No

Semicolon delimited list of email addresses to receive   
a notification from OnTrac when then shipment is   
delivered

CargoType

Integer

No

Currently always 0

An example in .Net is shown: System.Web.HttpUtility.UrlDecode(LabelString);

![background image](OnTrac Web Service Integration Specifications009.png)

Web Service Integration Specifications

9

Return Structure

The structure of the XML response is described OnTracShipmentResponse.xsd. Below is a brief description of the   
XML data elements and their formats.

Name

Format Description

UID

String

For customer use only to associate a response to a request

Error

String

Description of any error in creating the package

TransitDays

Integer Estimated days to the delivery date from the date of shipment

ExpectedDeliveryDate

Date

Expected Delivery Date in yyyyMMdd format

CommitTime

Time

Service commit time in HH:mm:ss format

ServiceChrg

Float

Delivery service charge

ServiceChargeDetails

Float

Container for charges embedded in the service charge

BaseCharge

Float

Base charge

AdditionalCharges

Float

Additional assessorial fees

AdditionalCharge

Float

Individual assessorial fee

AdditionalCharge/Description String

Description of assessorial fee

AdditionalCharge/Value

Float

Dollar amount of assessorial fee

SaturdayCharge

Float

Saturday Delivery Fee

FuelChrg

Float

Fuel surcharge amount

TotalChrg

Float

Sum of service and fuel charges

TariffChrg

Float

OnTrac published rate with no discounts or negotiated rates

Label

String

Base64 encoded string image of or printer code for an OnTrac   
shipping label for the requested package if requested

SortCode

String

3 or 4 character OnTrac Sort Code associated with the consignee Zip

RateZone

Integer OnTrac rate zone for the transmitted package

EXAMPLES

Example Request URL

https://www.shipontrac.net/OnTracTestWebServices/OnTracServices.svc/V7/37/shipments?pw=testpass

Example XML Request

\<

OnTracShipmentRequest

\>

\<

Shipments

\>

\<

Shipment

\>

\<

UID

\>

R6MJTD6K4NCZEAAAA

\</

UID

\>

\<

shipper

\>

\<

Name

\>

Shippers Inc.

\</

Name

\>

\<

Addr1

\>

55 First St

\</

Addr1

\>

\<

City

\>

Los Angeles

\</

City

\>

\<

State

\>

CA

\</

State

\>

\<

Zip

\>

90210

\</

Zip

\>

\<

Contact

\>

John Doe

\</

Contact

\>

![background image](OnTrac Web Service Integration Specifications010.png)

Web Service Integration Specifications

10

\<

Phone

\>

555-555-5555

\</

Phone

\>

\</

shipper

\>

\<

consignee

\>

\<

Name

\>

Con Ltd

\</

Name

\>

\<

Addr1

\>

555 Eastern Pkwy

\</

Addr1

\>

\<

Addr2

\>

Suite 77

\</

Addr2

\>

\<

Addr3

\>\</

Addr3

\>

\<

City

\>

Salinas

\</

City

\>

\<

State

\>

CA

\</

State

\>

\<

Zip

\>

90210

\</

Zip

\>

\<

Contact

\>

Jane Doe

\</

Contact

\>

\<

Phone

\>

555-555-5555

\</

Phone

\>

\</

consignee

\>

\<

Service

\>

C

\</

Service

\>

\<

SignatureRequired

\>

true

\</

SignatureRequired

\>

\<

Residential

\>

true

\</

Residential

\>

\<

SaturdayDel

\>

true

\</

SaturdayDel

\>

\<

Weight

\>

5

\</

Weight

\>

\<

BillTo

\>

0

\</

BillTo

\>

\<

Instructions

\>

Ring Bell

\</

Instructions

\>

\<

Reference

\>

Awe343

\</

Reference

\>

\<

Reference2

\>\</

Reference2

\>

\<

Reference3

\>\</

Reference3

\>

\<

Tracking

\>\</

Tracking

\>

\<

DIM

\>

\<

Length

\>

0

\</

Length

\>

\<

Width

\>

0

\</

Width

\>

\<

Height

\>

0

\</

Height

\>

\</

DIM

\>

\<

LabelType

\>

0

\</

LabelType

\>

\<

ShipEmail

\>\</

ShipEmail

\>

\<

DelEmail

\>\</

DelEmail

\>

\<

ShipDate

\>

2022-12-17

\</

ShipDate

\>

\<

CargoType

\>

0

\</

CargoType

\>

\</

Shipment

\>

\</

Shipments

\>

\</

OnTracShipmentRequest

\>

Example XML Response

\<

OnTracShipmentResponse

\>

\<

Error

\>\</

Error

\>

\<

Shipments

\>

\<

Shipment

\>

\<

UID

\>

R6MJTD6K4NCZEAAAA

\</

UID

\>

\<

Tracking

\>

D10013755557261

\</

Tracking

\>

![background image](OnTrac Web Service Integration Specifications011.png)

Web Service Integration Specifications

11

\<

Error

\>\</

Error

\>

\<

TransitDays

\>

1

\</

TransitDays

\>

\<

ExpectedDeliveryDate

\>

20221219

\</

ExpectedDeliveryDate

\>

\<

CommitTime

\>

17:00:00

\</

CommitTime

\>

\<

ServiceChrg

\>

20.54

\</

ServiceChrg

\>

\<

ServiceChargeDetails

\>

\<

BaseCharge

\>

8.94

\</

BaseCharge

\>

\<

PoundsCharge

\>

0

\</

PoundsCharge

\>

\<

AdditionalCharges

\>

11.6

\</

AdditionalCharges

\>

\<

AdditionalChargesDetails

\>

\<

AdditionalCharge

\>

\<

Description

\>

RESIDENTIAL DELIVERY

\</

Description

\>

\<

Value

\>

5.25

\</

Value

\>

\</

AdditionalCharge

\>

\<

AdditionalCharge

\>

\<

Description

\>

RESIDENTIAL SIGNATURE

\</

Description

\>

\<

Value

\>

6.35

\</

Value

\>

\</

AdditionalCharge

\>

\</

AdditionalChargesDetails

\>

\<

SaturdayCharge

\>

0

\</

SaturdayCharge

\>

\</

ServiceChargeDetails

\>

\<

RateZone

\>

2

\</

RateZone

\>

\<

BilledWeight

\>

5

\</

BilledWeight

\>

\<

FuelChrg

\>

0

\</

FuelChrg

\>

\<

TotalChrg

\>

20.54

\</

TotalChrg

\>

\<

TariffChrg

\>

26.38

\</

TariffChrg

\>

\<

Label

\>\</

Label

\>

\<

SortCode

\>

COM

\</

SortCode

\>

\</

Shipment

\>

\</

Shipments

\>

\</

OnTracShipmentResponse

\>

GET

An HTTP GET to this resource will return shipment details about one or more packages. Depending on the query   
string parameters you can either get tracking/POD information and update shipment information, or you can get   
only updated shipment details. The shipment information may change, once OnTrac has received the physical   
package, includes weight and charges, etc. Tracking requests are limited to 100 packages per request.

Parameters

Name

Required

Format

pw

Yes

String

requestType

Yes

"details" or "track"

logoFormat

No

BMP, GIF, PNG or JPG

sigFormat

No

PNG  
![background image](OnTrac Web Service Integration Specifications012.png)

Web Service Integration Specifications

12

tn

Yes

Comma delimited list of OnTrac tracking numbers or customer reference numbers

The "requestType" specifies the type of shipment update requested.

If "logoFormat" has a valid value, an OnTrac logo will be returned as a base64 encoded string in the requested   
format.

If "sigFormat" has a valid value, a POD signature will be returned as a base64 encoded PNG string. If a VPOD is   
available, the image will be returned as a base64 encoded PNG string.

\* Note -- These last two parameters are only available for tracking requests and not for details requests.

Return Structure

The structures of the XML responses are described OnTracTrackingResponse.xsd and OnTracUpdateResponse.xsd.   
Below is a brief description of the XML data elements and their formats.

Name

Format

Description

Event

String

A tracking event for the shipment

Status

String

\* OnTrac status code of the event

Description

String

A description of the OnTrac status code

EventTime

String

DateTime of the event

Facility

String

The name of the OnTrac facility at which the event occurred

City

String

OnTrac facility City

State

String

OnTrac facility State

Zip

String

OnTrac facility Zip

Tracking

String

OnTrac Tracking number of the shipment

Exp_Del_Date

Datetime

YYYY-MM-DD date that the package should be delivered

ShipDate

Datetime

Date that the package was shipped

Delivered

Boolean

Indicates the delivery status of the package

Name

String

Name of the consignee

Contact

String

Consignee contact

Addr1-3

String

Consignee address

City

String

Consignee city

State

String

Consignee state

Zip

String

Consignee Zip

Service

String

OnTrac Service Type

POD

String

POD name that the driver recorded if available

Error

String

Description of any error occurring while tracking the shipment

Reference

String

Shipment reference

Reference2

String

Shipment reference2

Reference3

String

Not currently used

Signature

String

Base64 encoded string of requested signature when available

Vpod

String

URL from where the VPOD image may be retrieved

Logo

String

Base64 encoded string of the OnTrac logo when requested

\* A list of the OnTrac Status Codes is available at the end of this document.  
![background image](OnTrac Web Service Integration Specifications013.png)

Web Service Integration Specifications

13

EXAMPLES

Example Request URLs

https://www.shipontrac.net/OnTracTestWebServices/OnTracServices.svc/V7/37/shipments?pw=testpass\&tn=D10  
010515798960\&requestType=track\&logoFormat=GIF\&sigFormat=GIF

https://www.shipontrac.net/OnTracTestWebServices/OnTracServices.svc/V7/37/shipments?pw=testpass\&tn=D10  
010515798960\&requestType=details

Example XML Response

TRACK

\<

OnTracTrackingResult

xmlns:xsi

="

http://www.w3.org/2001/XMLSchema-instance

"

xmlns:xsd

="

http://www.w3.org/2001/XMLSchema

"\>

\<

Shipments

\>

\<

Shipment

\>

\<

Events

\>

\<

Event

\>

\<

Status

\>

XX

\</

Status

\>

\<

Description

\>

DATA ENTRY

\</

Description

\>

\<

EventTime

\>

2022-04-06T14:53:21.45

\</

EventTime

\>

\<

Facility

\>

Commerce

\</

Facility

\>

\<

City

\>

COMMERCE

\</

City

\>

\<

State

\>

CA

\</

State

\>

\<

Zip

\>

90040

\</

Zip

\>

\</

Event

\>

\</

Events

\>

\<

Tracking

\>

D10010466126749

\</

Tracking

\>

\<

Exp_Del_Date

\>

2012-04-09T00:00:00

\</

Exp_Del_Date

\>

\<

ShipDate

\>

2012-04-06T00:00:00

\</

ShipDate

\>

\<

Delivered

\>

false

\</

Delivered

\>

\<

Name

\>

JOHN DOE

\</

Name

\>

\<

Contact

/\>

\<

Addr1

\>

580 LOMMEL ROAD

\</

Addr1

\>

\<

Addr2

/\>

\<

Addr3

/\>

\<

City

\>

CALISTOGA

\</

City

\>

\<

State

\>

CA

\</

State

\>

\<

Zip

\>

94515

\</

Zip

\>

\<

Service

\>

C

\</

Service

\>

\<

POD

/\>

\<

Error

/\>

\<

Reference

\>

TESTING

\</

Reference

\>

\<

Reference2

/\>

\<

Reference3

/\>

![background image](OnTrac Web Service Integration Specifications014.png)

Web Service Integration Specifications

14

\<

ServiceCharge

\>

11.25

\</

ServiceCharge

\>

\<

FuelCharge

\>

1.71

\</

FuelCharge

\>

\<

TotalChrg

\>

12.96

\</

TotalChrg

\>

\<

Residential

\>

false

\</

Residential

\>

\<

Weight

\>

3

\</

Weight

\>

\<

Signature

\>---\<

Signature

/\>

\<

Vpod

\>---\<

Vpod

/\>

\</

Shipment

\>

\</

Shipments

\>

\<

Note

\>

Results Provided by OnTrac at 10/11/2022 9:19 AM

\</

Note

\>

\<

Logo

\>---\</

Logo

\>

\<

Error

/\>

\</

OnTracTrackingResult

\>

DETAILS

\<

OnTracUpdateResponse

xmlns:xsi

="

http://www.w3.org/2001/XMLSchema-instance

"

xmlns:xsd

="

http://www.w3.org/2001/XMLSchema

"\>

\<

Shipments

\>

\<

Shipment

\>

\<

Tracking

\>

D10010466126749

\</

Tracking

\>

\<

Delivered

\>

false

\</

Delivered

\>

\<

ServiceCharge

\>

11.25

\</

ServiceCharge

\>

\<

FuelCharge

\>

1.71

\</

FuelCharge

\>

\<

TotalChrg

\>

12.96

\</

TotalChrg

\>

\<

Residential

\>

false

\</

Residential

\>

\<

Weight

\>

0

\</

Weight

\>

\</

Shipment

\>

\</

Shipments

\>

\</

OnTracUpdateResponse

\>

SHIPMENT ERRORS

<br />

Billing Account is Invalid or Does Not Allow Third Party Billing   
Delivery Zip Not Serviced   
Insufficient Consignee Address Information   
Insufficient Shipper Address Information   
Invalid Consignee City   
Invalid Consignee State   
Invalid Shipment Information (Invalid Data Format)   
Invalid Shipper City   
Invalid Shipper State   
Invalid Tracking Number   
Invalid Tracking String   
Invalid Username or Password   
Outside the Bounds of the Array (batch of shipments over 100)  
![background image](OnTrac Web Service Integration Specifications015.png)

Web Service Integration Specifications

15

Pickup Zip Not Serviced   
Saturday Service Unavailable for + ZIP   
Service Temporarily Unavailable   
The Requested Service Type is not Available For This Account   

\*Also, if the XML is malformed or errors out during deserialization an error will also be sent.

RATES

LOCATION

PRODUCTION   

https://www.shipontrac.net/OnTracWebServices/OnTracServices.svc/V7/{account}/rates   

TEST   

https://www.shipontrac.net/OnTracTestWebServices/OnTracServices.svc/V7/{account}/rates

\* Note -- {account} represents a valid OnTrac user account in the above URLs

AVAILABLE METHODS

GET

The GET method will return a rate quote for one or more packages as described in the query string. The body of   
the HTTP response will have an XML document containing the rate quote information as described in   
OnTracRateResponse.XSD. In the OnTrac system, there is no distinction between packages and shipments. Each   
package is treated as an independent unit. The web interface allows the user to rate more than one package in a   
single request, but the user must total the charges on the client side if that is their wish.

For example, rating three packages (p1, p2 and p3) will return three quotes (q1, q2 and q3). Determining the sum   
of the three quotes is the client's responsibility.

There is also an optional parameter "letter" to specify that the shipments in the request are to be rated as letters.   
This will cause any weights and/or dimensions in the request to be ignored. Letter rating can also be accomplished   
by simply passing in zeroes for the shipment weights and dimensions.

In addition, there is a Cargo Type parameter that may be used at the end of the request. Currently it is reserved for   
future use and should only be populated with a zero. If this parameter is to be passed, a 1 or 0 MUST be passed   
into the Letter parameter.

![background image](OnTrac Web Service Integration Specifications016.png)

Web Service Integration Specifications

16

Parameters

Name

Required

Format

pw

Yes

String

packages

Yes

\* String

\*Packages Parameters

The packages parameter is a comma separated list of packages that are to be rated.   
\&packages={package},{package}... e.g.

Each package itself is a list of parameters describing each package that is to be rated.

Below is a description of each of the parameters of a package

Name

Required Format

UID

Yes

For customer use only. This value is returned in the response

PUZip

Yes

5 digit origination Zip of the package

DelZip

Yes

5 digit destination Zip of the package

Residential

Yes

Boolean indicating if the package destination is residential

SaturdayDel

Yes

Boolean indicating if the package is for Saturday delivery

Weight

Yes

Weight of the package in lbs

DIM

Yes

Dimensions of the package in the format: (length)X(width)X(height)

Service

Yes

2 character OnTrac Service code. An empty service parameter will return   
quotes for all available services. C - Ground

Ship Date

No

MM-DD-YY formatted date of shipment

Package example:

...\&packages={UID;PUZip;Delzip;Residential;SaturdayDel;Weight;DIM;Service;ShipDate }

...\&packages=ID1;90212;93727;false;false;5;4X3X10;C;03-03-2023

This request will return a quote for:



UID = ID1



From 90210 to 93727



Non-residential delivery



Non Saturday Delivery



Weight of 5 pounds



Dimensions of 4 by 3 by 10 inches



Shipped using OnTrac Ground service

Return Structure

The structures of the XML response can be found in onTracRateResponse.XSD. Below is a brief description of the   
XML data elements and their formats.  
![background image](OnTrac Web Service Integration Specifications017.png)

Web Service Integration Specifications

17

Name

Format

Description

UID

String

For customer use only. This value is returned in the response

PUZip

String

5 digit origination Zip of the package

DelZip

String

5 digit destination Zip of the package

Residential

Boolean

Boolean indicating if the package destination is residential

SaturdayDel

Boolean

Indicates if the package is for Saturday delivery

Weight

Float

Weight of the package in lbs

DIM

Yes

Dimensional container

Length

Float

Package length in inches

Width

Float

Package width in inches

Height

Float

Package height in inches

ExpectedDeliveryDate

Date

Expected Delivery Date in yyyyMMdd format

CommitTime

Time

Service commit time in HH:mm:ss format

ServiceCharge

Float

Delivery service charge

ServiceChargeDetails

Float

Container for charges embedded in the service charge

BaseCharge

Float

Base charge

PoundCharge

Float

Additional weight fee

AdditionalCharges

Float

Additional assessorial fees

AdditionalCharges-Description String

Assessorial Description

AdditionalCharges-Value

Float

Assessorial Amount

SaturdayCharge

Float

Saturday Delivery Fee

FuelCharge

Float

OnTrac fuel surcharge

TotalCharge

Float

Sum of the service and fuel charges

TransitDays

Integer

Estimated days in transit

GlobalRate

Float

Total OnTrac delivery charge without negotiated rates or   
discounts

RateZone

Integer

OnTrac RateZone for the rated package

BilledWeight

Integer

The weight in pounds used to rate the package based on   
weight and DIM parameters

EXAMPLES

Example Request URL

https://www.shipontrac.net/OnTracWebServices/OnTracServices.svc/V7/37/rates?pw=testpass\&packages=1;9212  
9;93727;true;true;18.00;0.00X0.00X0.00;C;03-30-23

Example XML Response

\<

OnTracRateResponse

\>

\<

Shipments

\>

\<

Shipment

\>

\<

Rates

\>

\<

Rate

\>

\<

Service

\>

C

\</

Service

\>

![background image](OnTrac Web Service Integration Specifications018.png)

Web Service Integration Specifications

18

\<

ServiceCharge

\>

19.68

\</

ServiceCharge

\>

\<

ServiceChargeDetails

\>

\<

BaseCharge

\>

13.43

\</

BaseCharge

\>

\<

PoundsCharge

\>

0

\</

PoundsCharge

\>

\<

AdditionalCharges

\>

5.25

\</

AdditionalCharges

\>

\<

AdditionalChargesDetails

\>

\<

AdditionalCharge

\>

\<

Description

\>

RESIDENTIAL DELIVERY

\</

Description

\>

\<

Value

\>

5.2500

\</

Value

\>

\</

AdditionalCharge

\>

\</

AdditionalChargesDetails

\>

\<

SaturdayCharge

\>1\</

SaturdayCharge

\>

\</

ServiceChargeDetails

\>

\<

FuelCharge

\>

0

\</

FuelCharge

\>

\<

TotalCharge

\>

19.68

\</

TotalCharge

\>

\<

BilledWeight

\>

18

\</

BilledWeight

\>

\<

TransitDays

\>

1

\</

TransitDays

\>

\<

ExpectedDeliveryDate

\>

20230331

\</

ExpectedDeliveryDate

\>

\<

CommitTime

\>

17:00:00

\</

CommitTime

\>

\<

RateZone

\>

3

\</

RateZone

\>

\<

GlobalRate

\>

45.85

\</

GlobalRate

\>

\<

Error

\>\</

Error

\>

\</

Rate

\>

\</

Rates

\>

\<

UID

\>

1

\</

UID

\>

\<

Delzip

\>

93727

\</

Delzip

\>

\<

PUZip

\>

92129

\</

PUZip

\>

\<

Declared

\>

0

\</

Declared

\>

\<

Residential

\>

true

\</

Residential

\>

\<

SaturdayDel

\>

true

\</

SaturdayDel

\>

\<

Weight

\>

18

\</

Weight

\>

\<

DIM

\>

\<

Length

\>

0

\</

Length

\>

\<

Width

\>

0

\</

Width

\>

\<

Height

\>

0

\</

Height

\>

\</

DIM

\>

\<

Error

\>\</

Error

\>

\</

Shipment

\>

\</

Shipments

\>

\<

Error

\>\</

Error

\>

\</

OnTracRateResponse

\>

![background image](OnTrac Web Service Integration Specifications019.png)

Web Service Integration Specifications

19

ONTRAC SHIPPING LABEL FORMATION

<br />

An image of the OnTrac Shipping label is provided below, along with explanations of its various components. The   
Code 128-B symbol, the Code 128-C symbol and the PDF-417 symbol specifications, and associated data fields, are   
detailed in sections that follow. We prefer white label stock to be use, and require a white background in the areas   
where the barcodes are printed.   

18

17

16

15

14

13

12

1

2

3

4

5

6

7

8

9

10

11

<br />

![background image](OnTrac Web Service Integration Specifications020.png)

Web Service Integration Specifications

20

ONTRAC SHIPPING LABEL DIAGRAM

1.

Shipper Information

a.

Name, Address lines, City, State, and Postal Code -- Arial Bold, Caps 0.25 cm tall

2.

Label Creation Date -- Arial, 0.25 cm tall, Time component is optional

3.

Recipient Information

a.

Recipient Contact Name, Company Name, Address lines 1-3 -- Arial bold, Caps 0.3 cm tall

4.

Recipient City, State, Postal Code

a.

Arial, Bold, Caps 0.4 cm tall

5.

2D Barcode Symbol

a.

PDF-417 ANSI MH10

b.

Module Width -- x Dimension must be 10 mil

c.

Module Height -- y Dimension must be 5 times x Dimension at 50 mil

d.

Overall barcode width -- 9.0 cm

e.

Whitespace -- minimum of 0.5 cm between left and right label edges and barcode

6.

Shipper discretionary Area (optional)

a

. This area between line 15 and line 16 may be used as desired by Shipper for References, Purchase

Orders, Product ID, etc. Text, images, or symbols must be 0.40 cm below line 15, 0.4 cm above line 15,   
and 0.4 cm from both right and left label edges.

b.

For labels produced by OnTrac systems such as OnTrac Desktop Shipping and WebOnTrac, this area

will contain the Shipper's Reference1 and Reference2 information, if provided. The sample label   
presented above depicts this situation.

7.

Service Indication -- Arial, Reverse Bold, All Caps, 0.6 cm tall

.

Please see 18(f) below for Service Indicator

Translation Map.

8.

Actual Weight in LBS -- Integer-only weight and "LB" Acronym, Arial, Bold Caps, 0.3 cm tall

9.

Saturday Delivery Indicator - Arial, "SATURDAY" in Reverse Bold, All Caps, 0.30 cm tall (optional)

10.

Signature Required -- Arial, All Caps, 0.3 cm tall (optional)

11.

1D Barcode Symbol

a.

Code 128B -- Force Code 128 printing or leave minimum 1.2 cm white space between label edge and   
barcode on both right and left sides. Whitespace of minimum 0.2 cm between horizontal line 12 and   
top of barcode

b.

Barcode Modulus ("x") Dimension 15 mil

c.

Barcode overall Height 2.5 cm minimum

d.

ANSI Quality -- Minimum B

e.

Tracking Number Font: Arial bold, Caps 0.3 cm tall

12.

Line Horizontal -- Minimum 0.254 mm thick. Located 11.8 cm from top edge of label

13.

Sort Code for Destination -- Arial, Reverse Bold, All Caps, 1.2 cm tall

14.

OnTrac Logo Area Text

a.

"OnTrac" -- Arial Bold, Cap "O", small "n", Cap "'T", small "rac", Caps 0.4 cm tall

b.

"ontrac.com" -- Arial, all small letters, 0.15 cm tall

15.

Line Horizontal -- Minimum 0.254 mm thick. Located 9.0 cm from top edge of label

16.

Line Horizontal -- Minimum 0.254 mm thick. Located 6.8 cm from top edge of label

a.

Whitespace of variable size (dependent on barcode size) between horizontal line 16 and 2D barcode

b.

Whitespace of 0.35 cm between horizontal line 17 and 2D barcode

17.

Line Horizontal -- Minimum 0.254 mm thick. Locate 4.2 cm from top edge of label  
![background image](OnTrac Web Service Integration Specifications021.png)

Web Service Integration Specifications

21

18.

1D Barcode symbol representing two-digit Service Indicator code plus 5-Digit Delivery zip code. The two-  
digit service indicator shall be prefixed with a leading zero; no spaces.

a.

Code 128C

b.

Top of barcode located 0.3 cm from top edge of label. Right edge of barcode located 0.7 cm from

right edge of label

c.

Barcode Modulus ("x") Dimension 15 mil

d.

ANSI quality -- Minimum B

e.

Service Indicator Code translation map

f. Two Digit Code

Service Description

01

Ground

![background image](OnTrac Web Service Integration Specifications022.png)

Web Service Integration Specifications

22

SAMPLE LABELS

\* Note -- All labels must be certified by OnTrac before production use. Please send a sample label to

ont@ontrac.com

for approval.

![background image](OnTrac Web Service Integration Specifications023.png)

Web Service Integration Specifications

23

ONTRAC SHIPPING LABEL PDF-417 SYMBOL SPECIFICATIONS

<br />

The physical aspects of the OnTrac PDF-417 symbol have been chosen to give the various types of scanning   
equipment a high percentage chance of obtaining an accurate scan on each first attempt. Most PDF-417 symbols   
will be generated by off-the-shelf software, so the specification for the dimensions presented below should be   
basic configuration settings provided to these systems. White Label Stock should always be used to print PDF-417   
symbols for Shipping Labels.   

Module Height/Width

a.

X-Dimension (Module Width)

10 mil

b.

Y-Dimension (Module Height)

5 times X-Dimension at 50 mil

Number of Columns

a.

12 Columns wide (10 Data fields)

Aspect Ratio

a.

The Row-to-Column Aspect Ratio should be selected as low as possible in order to produce a rectangular   
barcode.

b.

A one-to-two ratio is suggested.

Width

a.

X-Dimension (Overall Symbol Width)

9.0 cm

Height

a.

Y-Dimension (Relative to X-Dimension)

Quiet Zone

a.

Top and Bottom 0.35 cm minimum

Error Correction

a.

Level 5

ONTRAC DATA STREAM FORMAT FOR ANSI MH10.8.3 COMPLIANCE

Description

Data Format

Max Data Length Notes

Message Header

\[)\>\<RS\>

Constant Value Indicating ANSI MH10.8.3   
Compliance

Format Envelope Header

01\<GS\>02

Transportation Format 01, Version 02

Recipient Postal Code

(an, 5 or 6)\<GS\>

5

Delivery Zip Code - 5 Digit

Recipient Country Code

(n, 3)\<GS\>

3

Always 840 for US shipments

Class of Service

(an,1-3)\<GS\>

3

Service Requested\*\*

Tracking Number

(an,15)\<GS\>

15

OnTrac Tracking Number

Origin Carrier SCAC

(an, 2-4)\<GS\>

4

EMSY for OnTrac

Account Number

(an, 1-8)\<GS\>

8

OnTrac Shipper Account Number

Julian Pickup Date

(n, 3) \<GS\>

3

For calendar year

Shipper ID Number

\<GS\>

Not used

Container n of Total of x

(n, 1-4/ n, 1-4)\<GS\>

3

Always 1/1

Weight in Pounds

(r, 1-8,2,a02) \<GS\>

10

Formatted as nnnnn.nnLB, leading zeroes   
not required

![background image](OnTrac Web Service Integration Specifications024.png)

Web Service Integration Specifications

24

Cross Match Zip Code to   
State

(a,1) \<GS\>

1

Always N

Recipient Address Line 1

(an, 1-30)\<GS\>

30

Street Number, Street Name, Suite, etc.

Recipient City

(an, 1-30)\<GS\>

30

Recipient State/Province

(an, 2)\<GS\>

2

Recipient Contact Name

(an,1-35)

35

Recipient Contact Name

Format Separator

\<RS\>

Constant Value - Format Separator

Format Envelope Header

06\<GS\>

Format Group 6, Category 26, Mutually   
Agreed-upon DI's

OnTrac Version Number

3Z(an,2)\<GS\>

2

OnTrac Barcode Version Identifier Current   
Version = 01

Ship To Company Name

11Z(an,1-25)\<GS\>

25

If no Company Name available, use   
Recipient Contact name

Ship To Phone Number\*

12Z(n,10)\<GS\>

10

Digits only, no parentheses or hyphens

Ship To Address Line 2\*

14Z(an,1-30)\<GS\>

30

Additional address info

Ship From Zip Code

15Z(an,5)\<GS\>

5

Origination zip code

Signature Required

21Z(n,1)\<GS\>

1

0=No; 1=Yes

Letter

22Z(n,1)\<GS\>

1

Always 0

3rd Party Billing Account #\*

23Z(n,1-8)\<GS\>

8

If Different from OnTrac Shipper Account   
Number provided above in format Group 1,   
otherwise pass 0

Saturday Delivery

24Z(n,1)\<GS\>

1

0=No, 1=Yes

Customer Reference\*

9K(an,1-30)\<GS\>

30

Customer generated Reference Number.   
Reference Field 1 data to be passed here.

Format Separator

\<RS\>

Constant Value -- Format Separator

Message Trailer

\<EOT\>

Constant Value -- Message Trailer

Notes:

an -- indicates alpha-numeric data; Value is a sequence of any printable characters   
a -- indicates alphabetic data   
n -- indicates numeric data; Value is a sequence of any digits   
r -- indicates radial data; Value is a sequence of any digits and a decimal point. Decimal point is not included for

whole numbers

\* Indicates optional use   
\*\* Valid service selection is: (01) Ground. Use the two-digit designations for MH10.8.3 data stream and print full

descriptions on the physical label.

NON-PRINTABLE ASCII CHARACTERS USED IN DATA STREAM

<br />

\<FS\>

Field Separator, Decimal 28

\<GS\>

Group Separator, Decimal 29

\<RS\>

Format Separator, Decimal 30

\<EOT\> End of Transmission, Decimal 04  
![background image](OnTrac Web Service Integration Specifications025.png)

Web Service Integration Specifications

25

ANSI MH10.8.3 DATA STREAM EXAMPLE

<br />

\[)\<RS\>01\<GS\>0285040\<GS\>840\<GS\>01\<GS\>D11214831957743\<GS\>EMSY\<GS\>37\<GS\>222\<GS\>\<GS\>1/1\<GS\>   
3LB\<GS\>N\<GS\>4440 E ELWOOD ST\<GS\>PHOENIX\<GS\>AZ\<GS\>CLYSPER ROSS\<RS\>06\<GS\>3Z01\<GS\>   
11ZONTRAC-CLYSPER ROSS\<GS\>12Z8887648888\<GS\>14ZSTE102\<GS\>15Z91752\<GS\>   
21Z1\<GS\>22Z0\<GS\>24Z1\<GS\>9KP12845329\<GS\>\<RS\>\<EOT\>

<br />

Data Stream Sample formatted below with Carriage Returns for readability purposes only

\[)\<RS\>   
01\<GS\>02   
85040\<GS\>   
840\<GS\>   
01\<GS\>   
D1214831957743\<GS\>   
EMSY\<GS\>   
37\<GS\>   
222\<GS\>   
\<GS\>   
1/1\<GS\>   
3LB\<GS\>   
N\<GS\>   
4440 E ELWOOD ST\<GS\>   
PHOENIX\<GS\>   
AZ\<GS\>   
CLYSPER ROSS   
\<RS\>   
06\<GS\>   
3Z01\<GS\>   
11ZONTRAC-CLYSPER ROSS\<GS\>   
12Z8887648888\<GS\>   
14ZSTE102\<GS\>   
15Z91752\<GS\>   
21Z1\<GS\>   
22Z0\<GS\>   
24Z1\<GS\>   
9KP12845329\<GS\>   
\<RS\>   
\<EOT\>   

![background image](OnTrac Web Service Integration Specifications026.png)

Web Service Integration Specifications

26

ONTRAC SHIPPING LABEL CODE 128-C ROUTING SYMBOL SPECIFICATIONS

The physical aspects of the OnTrac Code 128-C, one-dimensional barcode are listed below.   

1.

Barcode modulus ("X") dimension 15 mil

2.

Barcode Height

1.9 cm

3.

ANSI quality

Minimum B

Barcode Content

<br />

The Code 128-C Routing symbol will contain a leading zero plus a two-digit encoded service indicator plus the five-   
digit zip code of the delivery address, as itemized below.   

Position 1

Always 0

<br />

Positions 2-3

Two digit Encoded Service Indicator. Valid service selection is: (01) Ground

<br />

Positions 4 -- 8 Five digit Zip code of Delivery address

ONTRAC SHIPPING LABEL CODE 128-B TRACKING NUMBER SYMBOL SPECIFICATIONS

<br />

The physical aspects of the OnTrac Code 128-B, one-dimensional barcode are listed below.   

1.

Barcode modulus ("X") dimension 15 mil

2.

Barcode Height

2.5 cm

3.

ANSI quality

Minimum B

<br />

The OnTrac Code 128-B barcode symbol shall include the 15 character OnTrac tracking number. The human-  
readable representation of this information will look similar to D10734902081420

ONTRAC TRACKING NUMBER

OnTrac uses a 15-character tracking number consisting of the character 'D' plus a 6-digit sequence number that   
OnTrac will assign, plus a 7-digit sequence starting at 1, plus one check digit.   

The 6-digit sequence number that we provide will remain static throughout a range of 0-9999999 tracking   
numbers.   

Each unique tracking number will be generated by the customer's shipping system, utilizing the 7-digit range,   
beginning with 0000001 and ending with 9999999.   

This format provides a range of 9,999,999 tracking numbers per each assigned 6-digit sequence. After the range of   
9,999,999 has been used, OnTrac will assign a new 6-digit static range.   

Example: D 154113 1441672 7  
![background image](OnTrac Web Service Integration Specifications027.png)

Web Service Integration Specifications

27

First character is always D   
Next 6 characters, 154113, is the static 6-digit sequence assigned by OnTrac   
Next 7 characters, 1441672, is the 7-digit sequence customer uses to generate unique tracking numbers   
Last digit, 7, is the calculated check digit   

The customer's shipping system must assign unique tracking numbers to each shipment. Below we will   
demonstrate how to calculate the check digit when utilizing our tracking numbers.

CHECK DIGIT CALCULATION

<br />

1.

Convert the initial alpha character to its numeric equivalent, which is always 4 for "D"

2.

From left, add all odd positions.

3.

From left, add all even positions.

4.

Multiply result of step three by 2.

5.

Add results of steps two and four.

6.

Subtract result from the next highest multiple of 10.

7.

The remainder is your check digit.

CHECK DIGIT EXAMPLE 1

<br />

Tracking number without check digit: D 100100 0000001   
1.

Convert the alpha character to its numeric equivalent: 4 100100 0000001

2.

From left, add all odd positions: 4 + 0 + 1 + 0 + 0 + 0 + 0 = 5

3.

From left, add all even positions: 1 + 0 + 0 + 0 + 0 + 0 + 1 = 2

4.

Multiply the result of step three by 2: 2 x 2 = 4

5.

Add results of steps two and four: 5 + 4 = 9

6.

Subtract result from the next highest multiple of 10: 10 -- 9 = 1

7.

The remainder is the check digit: 1

Result: D 100100 0000001

1

CHECK DIGIT EXAMPLE 2

<br />

Tracking number without check digit: D 175435 5831526   
1.

Convert the alpha character to its numeric equivalent: 4 175435 5831526

2.

From left, add all odd positions: 4 + 7 + 4 + 5 + 8 + 1 + 2 = 31

3.

From left, add all even positions: 1 + 5 + 3 + 5 + 3 + 5 + 6 = 28

4.

Multiply the result of step three by 2: 28 x 2 = 56

5.

Add results of steps two and four: 31 + 56 = 87

6.

Subtract result from the next highest multiple of 10: 90 -- 87 = 3

7.

The remainder is the check digit: 3

Result: D 175435 5831526

3

CHECK DIGIT EXAMPLE 3

<br />

Tracking number without check digit: D 100100 0000011  
![background image](OnTrac Web Service Integration Specifications028.png)

Web Service Integration Specifications

28

1.

Convert the alpha character to its numeric equivalent: 4 100100 0000011

2.

From left, add all odd positions: 4 + 0 + 1 + 0 + 0 + 0 + 1 = 6

3.

From left, add all even positions: 1 + 0 + 0 + 0 + 0 + 0 + 1 = 2

4.

Multiply the result of step three by 2: 2 x 2 = 4

5.

Add results of steps two and four: 6 + 4 = 10

6.

Subtract result from the next highest multiple of 10: 20 - 10 = 10

7.

The remainder is the check digit:

IF TEN, THE CHECK DIGIT IS ZERO

Result: D 100100 0000011

0

ONTRAC STATUS CODES

Status Code

Description

AI

Details needed. Please contact us.

AN

Delayed. Delivery date updated.

BW

Weather delay. See service alerts.

CA

Delivery address updated by sender.

CL

Delivered.

CO

Business closed. Please provide hours.

CR

Refused or returned. Contact sender.

DC

Damaged. Contact sender.

DD

Received damaged but delivered.

DI

Delivery date updated by request.

DN

Delivered to neighbor.

DR

Delivery not possible. Contact sender.

DW

Delivered.

ER

Wrong delivery status. Update pending.

HO

Attempted; recipient closed for holiday.

HP

Held for pickup at the local facility.

HW

Details needed. Please contact us.

LC

Cannot deliver. Contact sender.

LM

Delayed. Delivery date updated.

LR

Delayed by road closure.

LW

Weather delay. Delivery date updated.

MC

Wrong ZIP Code. Corrected; re-shipped.

MR

Misrouted. Delivery date updated.

MS

Misrouted. Delivery date updated.

NH

Delayed. Delivery date updated.

OD

Out for delivery.

OE

Shipping information transmitted.

OK

Delivered.

OS

Package en route.

PS

Package scanned at delivery facility.  
![background image](OnTrac Web Service Integration Specifications029.png)

Web Service Integration Specifications

29

PU

The package was picked up.

RB

Delayed. Delivery date updated.

RD

Packaged received at the facility.

RS

Returned. Contact sender.

SD

Out for delivery soon.

UD

Damaged. Contact sender.

UG

Need gate code. Please contact us.

UM

Returned. Contact sender.

WA

Wrong address. Please contact us.

XX

Order information created.

Revised 09-20-23

