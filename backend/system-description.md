Requirements Document for Waterstons SE Project
Group 22

1 - Intro
1.1 - Overview and Justification
Waterstons have proposed a system to automate monthly expense reports for their employees,
the software specified would scrape information from receipts and invoices using AI models and
provide a CSV file with all the necessary information - including date, merchant, amount and
tax. This software would benefit the concurrent and future employees at Waterstons as their
current system requires each employee to manually input the data, which they have found to be
time-consuming and error-prone for many of their employees. Within Waterstons our main
contact is Andrew Buckingham who is the Lead Software Consultant at the company,
accompanied by Frankie Clipsham who is a Software consultant focusing on their client’s
businesses. This document will outline how our group’s solution will meet the client’s
requirements, our chosen software development methodology, and our schedule for the
forthcoming duration of the project.
1.2 - Project Scope
Waterstons’ have requested a web application that when it receives a wide range of file formats,
including PDF, JSON, Image formats, can review the information within and produce a CSV file
containing all the relevant financial information needed. There are challenges included such as
being able to read and accurately format poor-quality or hand-written images ensuring that a
level of certainty is maintained. This would all be handled through a web interface designed to
be friendly to the user and easy to understand and fill out, allowing for verifications or
adjustments of the automated filing system. We plan to meet all of these requirements through
our methodology. We are aware that we are making this for Waterstons employees, therefore
we want to make it easily adaptable to the systems they have in place. As our solution will allow
Waterstons employees to handle their documents with less hassle and more efficiency allowing
them to prioritise their time on other projects. We plan to hold the data in a database making it
easily accessible and able to be connected to their systems and allow them to be processed
and analysed as needed. With our solution to this project we feel that it will create a reliable
process for their employees to increase their efficiency and accuracy when dealing with their
financial data.
1

1.3 - System descriptions
We proposed the whole solution to take the form of a web application with a server-client
architecture. We chose Nginx as the web server due to its superior performance compared to
Apache, particularly for handling high numbers of concurrent connections. We will host the
Django codebase using WSGI. An Optical Character Recognition (OCR) Engine is needed for
parsing receipt images. Tesseract is among the engines we are considering. Its flexibility allows
us to fine-tune it specifically for receipt parsing and its beginner-friendly documentation makes it
an accessible choice. However there are many more engines left to be considered such as
Kraken, EasyOCR, Doctr, and many more. For the server codebase, we chose Django because
it is more accessible for the team, and facilitates rapid development.
Moreover, the frontend will be developed using the React framework with Tailwind CSS to build
a responsive and scalable user interface. React’s component-based architecture allows us to
create reusable elements, streamlining the underlying nuances of frontend development.
Tailwind CSS, with its utility first approach, speeds up styling, by providing predefined classes,
making rapid development of consistent designs possible without having to write extensive CSS
from scratch. REST APIs will be established, ranging from general web requests to storage
transactions. Vite will be applied as the build solution.
Additionally, the web application will have its backend modular in design, particularly with regard
to the libraries that will be written. MongoDB will serve as the primary database, and will also be
the storage solution for receipt files, leveraging its GridFS feature to handle large files efficiently
and securely. OCR Engine will run inside Django, and will be configured accordingly for the
purpose of parsing receipt images. Django will handle file uploads. PDF Files will be converted
to an image, and will be preprocessed and then parsed like any other image. If the file is in
JSON, then it is stored right away in the GridFS Collection. The extracted data from the
uploaded files will be stored within a separate Collection, while the metadata, and other file
related information, will be stored on another separate Collection.
Lastly, the backend architecture will consist of two distinct web server instances: the General
server and the File Parsing server, both written in Django. The concerns surrounding the file
parsing will only be handled in the File Parsing server as well as the storing of the uploaded file
while all other tasks will be handled by the General server. The General server will be
concerned with general duties like fetching employee data, authentication, serving static files,
and fetching the blob items from the MongoDB collection. The core duty of the File Parsing
server is to parse files. The file parsing server has the ability to temporarily store uploaded files
using Django’s session-based file handling, after processing the upload. The file will persist until
they are confirmed or discarded. The result will then be sent to the frontend. If confirmed, the
frontend will send a request containing a confirm flag to the File Parsing server REST API, and
then the File Parsing server saves it. If not confirmed or if there was no request received
referring to the file then the temporarily stored file will be deleted.
2

2 - Solution Requirement
2.1 - Requirement Elicitation
Upon receiving the project brief, our team held an initial internal meeting to brainstorm
requirements using Agile methodologies. We began by drafting high-level user stories to capture
primary user needs and defined the features necessary to achieve the intended behaviour of the
application. However, we encountered challenges in interpreting certain parts of the brief, as
some user interactions and functionality requirements were unclear. For instance, it was initially
ambiguous whether the app was meant to be a standalone app or integrate with an existing
one.
Following this brainstorming phase, we created a rough project outline that mapped out the
intended user experience and highlighted areas needing clarification. To validate our
assumptions, ensure alignment with the client’s expectations we emailed the client with specific
questions to clarify uncertainties and confirm our understanding. The client’s responses
provided essential details about key features and intended user experiences, helping us refine
aspects of the user journey and better define the project’s scope.
With this feedback, we refined our project outline and user stories, focusing on aligning them
with the clarified requirements. In the client’s response, they also specified priority features,
such as robust data extraction from various image formats, including low-quality images, while
categorising currency conversion as a stretch goal. Initially, we had assumed this to be
essential, but adjusted our plan based on this clarification. This prioritised feature list allowed us
to focus on implementing core functionalities and plan our technical approach, including drafting
preliminary Gherkin scenarios to outline specific user interactions.
To gain deeper insight into the user’s perspective, we scheduled an in-person meeting with the
client to discuss requirements and the intended user experience in greater detail. This meeting
provided an opportunity to present our proposed features, validate our user stories with the
client, and resolve any remaining ambiguities. Although scheduling conflicts and health issues
prevented two team members from attending, we documented key points and shared updates
with the absent members, ensuring that our team remained aligned on the project’s plans and
directions.
During the on-site meeting, the client provided valuable insights into the users’ daily workflows
and specific needs, such as the required data export format. This led to further internal
discussions, where we refined our project priorities and finalised key features. Following this, we
updated our user stories and developed Gherkin scenarios to precisely capture this functionality,
ensuring our specifications closely aligned with the client’s expectations and clearly outlined
essential interactions and behaviours for implementation. Additionally, we confirmed the
technology requirements to implement these features and categorised them by priority, helping
us determine which features to focus on first.
3

2.2 - Behaviour requirement
Feature - Process text from any file format
Behavioural Requirement - The behavioural requirement for this feature is that the system must
read and convert any file the user uploads—whether it’s a well-formatted PDF table, an image of
a ticket, or a handwritten receipt—into usable text and data.
User Story - As a user, I want the system to extract data from any uploaded file, regardless of
type or quality, so I can trust the extracted data is accurate. I should also be notified if any
issues arise during the data extraction process.
BR1: File Upload
BR1.1: Successful extraction
Scenario: Successful data extraction from uploaded file
Given a user uploads a file
When the file is converted into a usable format
And the converted file is sent to the data extractor
And relevant information is scanned and extracted from the file
And the extracted data is validated
Then the data is sent to the frontend
And the system alerts the user that extraction was successful
BR1.2 : Failed extraction
Scenario: Data extraction failure
Given a user uploads a file
When the file is converted into a usable format
And the converted file is sent to the data extractor
And data cannot be extracted or validation fails
Then an error message is sent to the frontend
And the system alerts the user that an issue occurred during extraction
Rationale and Prioritization - This feature is a “Must-have” because it fulfils the client's primary
requirement of simplifying data entry by automating data extraction from various file formats. By
reducing manual data input, this feature improves accuracy and efficiency, aligning directly with
the client’s objectives and the project’s core functionality.
4

Feature - Export Database Data to CSV/JSON Format
Behavioural Requirement - The behavioural requirement for this feature is to enable the user,
upon completing data extraction from uploaded files, to convert and save all extracted data in
CSV format.
User Story - As a user, after I have finished uploading all my files and confirmed their accuracy, I
want to convert the extracted data into a CSV file. I should have the option to view and save this
CSV file for further use.
BR2: CSV formatter
BR2.1: Successful conversion
Scenario: Successfully convert database to CSV format
Given the user clicks "Convert to CSV"
When the database is inspected and the data is formatted as CSV
Then the system saves the CSV file
And the system alerts the user that conversion was successful
And the CSV file is sent to the frontend for the user to view
BR2.2: Failed conversion
Scenario: Unsuccessful conversion of database to CSV
Given the user clicks "Convert to CSV"
When the database is inspected
And the system detects an issue preventing conversion
Then the system alerts the user of the problem
Rationale and Prioritization -This feature is a “Must-have” as it fulfils the client’s core
requirement of creating a formatted file that can be shared with their finance team for auditing.
By automating data formatting, this feature supports the client’s objectives of saving user time
and providing a consistent format that simplifies auditing. This aligns with the client’s goal of
streamlining data transfer to the finance team, reducing manual input, and ensuring data
consistency.
5

Feature: User upload file
Behavioural Requirement - The behavioural requirement for this feature is that the system must
allow the user to upload different file types (e.g., images, PDFs) for automated processing. The
uploaded file should then be converted to a usable format for data extraction no matter its file
type.
User Story - As an employee, I want to upload a file containing receipt data so that the system
can automatically process and convert the file into editable data, allowing me to review and edit
the extracted information to ensure its correctness.
BR3: Receipt Upload
BR3.1: Successful upload
Scenario: Successful upload of receipt file
Given user is on upload page
When user selects valid receipt file
The user clicks upload button
Receipt file should now be uploaded
System will display preview of scanned data
BR3.2: Unsuccessful upload
Scenario: If scanner unable to use the file uploaded
Given the user is on the upload page
When the user selects invalid file format
And the user clicks on the upload button
Then the user should see an error message indicating wrong file format
Rationale and Prioritization - This feature is a “Must-have” because it directly enables the user
to start the invoice creation process allowing the system to handle multiple file types and
notifying the user of any file type errors, contributing to the main goal which is simplifying data
entry and reducing manual input.
6

Feature: User edit details
Behavioural Requirement - The behavioural requirement for this feature is that the system must
enable users to verify and manually edit details scanned from uploaded receipts. This provides
a crucial step in the process which will help increase accuracy.
User Story - As an employee, I want to verify and edit the scanned details from the receipt so
that I can ensure accuracy before sending it to the database.
BR4: User edit details
BR4.1: Editing scanned detail
Scenario: correcting scanned price details
Given the receipt details are displayed after upload
When user notices an incorrect data
And user manually enters correction
Then the updated price should be saved
BR4.2: Editing empty field
Scenario: Verifying all fields are correctly scanned
Given the receipt details are displayed after upload
When the user reviews all fields
If user notice a empty field
Then the user can edit the field as needed
And the system saves the updated information
Rationale and Prioritization - Allowing users to manually edit and manually input data is a
“Must-have” feature as it ensures correctness of data used for invoice generation. Minimising
errors and the need for corrections later. This directly supports the project's goals of creating
reliable and precise data CSV, contributing to improved data accuracy.
7

FEATURE: Live Location Tracker and Encoding
Behavioural Requirement: The web app must run within a web browser wherein there exists a
browser API for accessing the user’s current location. Such that the web app in turn will have
access to real-time location tracking and encoding. This will enable users to associate receipts
with where it was uploaded.
User Story: As a user, as I confirm the parsing of the file receipt, I want the system to capture
and encode my current location automatically and associate that to my file receipt upload, such
that I can maintain records that are linked to specific places.
BR5: Live Location Tracking and Encoding
BR5.1: Automatic Location Capture
Scenario: Capturing location on receipt upload
Given the user is already in the “confirm parsed content” page
When the web app has permissions to access location
Then it captures the user’s current location
And encodes it as the metadata for file upload.
BR5.2: Location Permission denied by user
Scenario: Handling location access denial
Given the user denies location access
When the app attempts to capture location
Then it prompts the user with an option to enable location tracking
And proceeds without location encoding if access is still denied.
But proceeds with location encoding if access is allowed
BR5.3: Location update on reupload
Scenario: Reuploading an existing receipt
Given Location access is allowed
When the user has confirmed the reupload of an existing entry
Then the web app prompts if the user would like to update location with
the current location.
Rationale and Prioritization - Live location tracking is “Should-have” as it enhances the
relevancy of the data of entry, letting the possibility to identify patterns and trends, ultimately
contributing to a more transparent record-keeping.
8

FEATURE: Login feature
Behavioural Requirement: The behavioural requirement for this feature is that the system has to
allow each user to have an account linked to their uploads and expenditure reports. The system
should be able to verify each user securely and allow for access for authorised users.
User Story: As an employee, I get clear access to my invoices and receipts and it does not
clash with other users making my expenses easier to track.
BR6: Users can register on the system
BR6.1 - Account creation
Scenario: The user is able to enter their email and password
The details are encrypted
They are sent over to a database
Details can then be used to login if verified
BR6.2 - Login
Scenario: User enters their details into the login box
If they match with the database access is granted
else they are prompted to reset their password
If no account is detected then prompted to make one.
Rationale and prioritisation - Allowing the users of the system to login in would be a “should
have” feature as it would be a lot more convenient for the user to have all of their information
saved and previous uploads available, it could also prompt to enter employee name or ID
number during the upload each time, making this not a must have feature.
9

Feature: Information Saved Into Database
Behavioural Requirement - The behavioural requirement for this feature is that the system must
save information (both the scanned text and the uploaded file) into a database. The information
stored must be saved along with the uploaded file, incase verification of the invoice is needed,
or incase discrepancies in the company's finances arise.
User Story - As an employee, I want the analysed text to be saved into a database, along with
the invoice or receipt image/file itself, so that the information can be reviewed later if needed.
BR8: Information Saved Into Database
BR8.1 - Saving text
Scenario: Saving scanned text into the database
Given the details have been verified and edited as needed
When user has confirmed these details to be correct
Then save this information in the database
BR8.2 - Saving image/file
Scenario: Saving the invoice or receipt image/file into the database
Given a invoice or receipt image/file has been uploaded
When scanned text has been saved into database
Then store the corresponding invoice or receipt image/file along with it
Rationale and Prioritization - Saving the text retrieved from the analysed file, as well as the
corresponding invoice or receipt image/file, allows for organised records to be kept. This is
useful when Waterstons needs to check these expenses, as they will be automatically organised
and structured, making their internal processes more efficient and less time consuming.
This is a “must have” as it ensures that Waterstons has a record of all the expenses and
invoices being submitted by its employees, as well as the evidence to go with it.
10

Feature: Responsive Web Interface For PC/Mobile
Behavioural Requirement - The behavioural requirement for this feature is that the web app
should be responsive and flexible across different platforms. For example, the mobile interface
is more restrictive, with less screen space when compared to PC, therefore the mobile interface
should incorporate methods to maintain functionality despite this disadvantage.
User Story - As an employee, I want an efficient experience when filing my invoices and receipts
from both my mobile and computer.
BR9: Responsive Web Interface For PC/Mobile
BR9.1 - PC responsiveness
Scenario: Opening the web app on a PC
Given the user is opening the web app on a PC
When the web app loads the interface
Then the app should adapt
And make use of the available space on a bigger screen
BR9.2 - Mobile responsiveness
Scenario: Opening the web app on a mobile
Given the user is opening the web app on a mobile
When the web app loads the interface
Then the app should adapt
And efficiently use the less available screen space on mobile
And while still maintaining functionality and usability
Rationale and Prioritization - A responsive interface that world seamlessly across different
layouts like mobile and PC, will allow employees to upload their receipts and invoices from
different platforms. This is useful because employees may not always have access to a specific
platform, this therefore allows them to upload and manage their invoices however they want.
This is a “Should-have”, as while functionality across platforms is required, its responsiveness is
not essential to the core experience of the service. However, it is still a high priority for the
product.
11

Feature: Poor Quality Images and Incomplete Receipt Handling
Behavioural requirement - The behavioural requirement for this feature is that the system must
be able to process and account for receipts that may be incomplete (missing information such
as VAT, Tax Breakdown, etc.), or of poor image quality. The system should attempt to extract all
readable data and notify the user of any unreadable and missing fields, for the user to intervene.
User story: I want to ensure that the encoding process leaves no chance for inaccuracy. Such
that I can still submit reliable information.
BR10: Handling Low-Quality Images and Missing Information
BR10.1: Pre-processing Images
Scenario: Enhancing image upload, and adjusting OCR parameters
Given the uploaded image is any uploaded image
While the pre-processing step starts
And and the system detects the deficiencies of the upload
Then the system enhances the image accordingly
And OCR is configured accordingly with predefined profiles
BR10.2: Low Quality Image Detection
Scenario: Identifying a low-quality image during processing
Given the user uploads a receipt file
When the system detects that the image quality is poor
Then the OCR still attempts to parse readable information
And the web app will still prompt for manual intervention for the
low-quality fields
BR10.3: Missing Field Notification
Scenario: Notifying user about missing or incomplete fields
Given the OCR is processing the receipt file
When the parsing finishes
Then the web app will prompt for manual intervention for the missing
fields.
Rationale and Prioritization - This feature is a “Should-have” as it allows for greater flexibility in
real-world scenarios where not all receipts meet the ideal quality. It minimises the need for
reuploads and mistakes due to quality and completeness issues, ensuring that the process
remains efficient and accurate.
12

3 - Project Management
3.1 - Risks and Issues
One significant risk we have identified is a technical risk associated with implementing computer
vision. Since our project relies heavily on an accurate computer vision model to extract data,
any failure in implementation would critically impact our ability to meet the project’s functional
requirements. However, none of our team members have prior experience working with
computer vision. Therefore, we assess the impact of this risk as high, as an ineffective model
could undermine the core functionality of our project. Nevertheless, after researching available
computer vision technologies and assessing their ease of implementation, we conclude that the
risk probability is low due to the abundance of accessible learning resources. To mitigate this
moderate risk, we are adopting proactive measures: we plan to conduct further research, select
an appropriate technology as soon as possible, and ensure that each team member dedicates
time to learning and familiarising themselves with it. Additionally, as each member gains
knowledge, we plan to have members who grasp the technology first to assist and teach other
members. This approach aims to minimise the risk's chances of happening.
Another risk we anticipate is a lack of sufficient test data, which is essential for validating our
data extraction model. Our project is designed to handle various file types, including receipts in
multiple formats and even handwritten receipts. Ensuring the model's accuracy across these
different formats requires extensive test data. However, the client has indicated that they may be
unable to provide a large dataset due to confidentiality concerns. We assess the probability of
this risk as high, with a moderate impact on our project’s. In response, we plan to prioritise this
risk. Our proactive risk management plan involves each team member collecting personal
examples, such as receipts from train tickets or grocery purchases, to build our own test data.
Additionally, we intend to request “pseudo” test data from the client, which would mimic real data
without compromising confidentiality. By taking these actions, we aim to minimise any potential
data shortage issues.
Lastly, we face a business risk related to the possible accidental overuse of cloud service
credits. Our project will rely on Azure cloud services, and there is a possibility that a coding error
could inadvertently exceed our credit limit. Although we assess this risk as having a low
probability, it could have a moderate impact on our project if we exceed the allocated budget. To
mitigate this, we have implemented an agile code review process on GitHub, ensuring that any
major bugs are identified and resolved before merging code to the main branch in Git.
Additionally, should we exceed our cloud credit limit, we have options to request additional funds
from our lecturer, who has indicated support for funding our project. Therefore, we have opted
for both a reactive and proactive approach to this risk, knowing that support from Azure or the
lecturer would allow us to address any budgetary concerns and that our code reviews before
merging will help prevent such issues.
13

3.2 - Development Approach
For this project, we have chosen an Agile approach, specifically using the Scrum methodology.
The approach we have selected is well-suited for our requirements due to the projects’ need for
flexibility, regular feedback, and iterative development, ensuring that we consistently meet our
expectations. Agile allows us to prioritise client feedback and make adjustments with each
sprint, enabling the team to remain aligned with the clients vision.
The Scrum framework will break down the project into two-week sprints, each starting with sprint
planning to set precise objectives and ending with a review for feedback. This process
prioritises that the development remains focused and responsive to the project's goals. Usual
stand up meetings will be held to track progress, address issues and maintain open
communication between the team.
Our first sprint will prioritise the photo scanning feature, as it forms the foundation of the system.
This feature is critical because it enables the initial data extraction process from the uploaded
receipts. By introducing and refining photo scanning first, we make sure that the systems’ core
functionality is accurate.
14

3.3 - Project Schedule
Requirement/Planning Phase: 21st October - 24th November 2024
● Discuss skills and abilities of team members - Allocate work and roles within the group.
● Communicate with clients - Gather requirements.
● Finalise the scope of the project, with help from the client.
● Confirm requirements with clients before moving on with development.
Academic Deadlines:
● Requirement Documentation, Peer Evaluation 1 (21st November 2024)
Development Phase 1: 25th November 2024 - 7th February 2025
Stage 1 (25th Nov - 8th Dec 2024)
○ Image/File Upload - Should be compatible with images, PDFs, email, etc.
○ Database Integration - Should store the uploaded files.
Stage 2 (9th Dec - 22nd Dec 2024)
○ File Analysis - Building framework that extracts data from files.
○ Data Organisation - Suitable organisation of the extracted data for database.
Stage 3 (6th Jan - 19th Jan 2025)
○ Login System - Allow users to have records of their own expense uploads.
○ Compatibility with different devices - Optimised for web and mobile.
Academic Deadlines:
● Test Plan Documentation, Peer Evaluation 2 (7th February 2025)
Development Phase 2: 3rd February - 21st March 2025
Stage 1 (3rd Feb - 16th Feb 2025)
○ Exporting Data to CSV/JSON - Allows clients to verify the uploaded expenses.
○ Manual Edits - Allows users to change information if recognition is incorrect.
Stage 2 (17th Feb - 2nd Mar 2025)
○ Location Tracker - To match expense claims with actual expenses on record.
○ Poor File Quality - Allows poor quality file uploads to still be analysed.
Academic Deadlines:
● Technical Report, Peer Evaluation 3 (14th March 2025)
● Product Presentation (w/b 17th March)
Product Finalisation and Handover: 17th March - 2nd May 2025
Stage 1 (17th Mar - 6th Apr 2025)
○ User testing, debugging, and finalising product using client feedback.
Stage 2 (7th Apr - 27th Apr 2025)
○ Documentation and preparation for deployment.
Academic Deadlines:
● Reflective Experience Report, Git Commit, Product Handover (2nd May 2025)
15
