# Welcome to ***"Properly"***!
___
## Introduction
"Properly" is a **web-based** rental property management information system, that is responsible of keeping track, add and provide valuable information concerning Properties, Contacts, Leases, Invoices and Payments.

The power of Properly is in it's ability to help users, whether they were Landlords or Property Managers, to get the most out of their Properties, initially by providing some valuable information on the fly, such as Occupancy rate and the count of invoices that are outstanding(passed their due date) in the main dashboard, in addition to multiple views that filters and lists entities such as properties or contact eg, based on some specific criterias, as I'm going to explain later.

___

## Technical Specifications
This application was built on visual studio code using:
* Languages:
    * Python
    * SQL
    * HTML
    * CSS
* Frameworks:
    * Back-end : Flask
    * Front-end: Bootstrap

___

## Product Desctiption
Properly consists of four main modules each is responsible for managing some kind of entity, these four modules are:
* Properties
* Contacts
* Leases
* Accounting

Modules mentioned above share some commonalities in term of functionality,
each of those has:
### Commonalities
* Add new record (each)
* Delete existing record (each)

And here I'll be recalling set of views or filters associated with each module, describing some of module's functionalities:

* ### Properties
    * All Properties: lists all properties owned by the current user.
    * Available Properties: lists properties that have no currently active lease.
    * Occupied Properties: lists properties having a currently active lease.
    * Deleting a Property will result in the deletion of all of data related to it.


* ### Contacts
    * All Contacts: lists all contacts owned by the current user.
    * Currently Leased: lists contacts having a currently active lease.
    * Deleting a contact will result in the deletion of all of data related to it.

* ### Leases
    * All Leases: lists all leases owned by the current user.
    * Active Leases: lists leases that intersects the current day.
    * Upcoming: lists leases that their start date is equal or greater than the current day.
    * Past Leases: lists leases that their end date is less than the current day.
    * Deleting a lease will result in the deletion of all of data related to it.
    * Adding a new lease requires the system check if the provided dates intersects some other existing lease so it return an apology to the user informing him/her of that.

* ### Accounting
    * All Invoices: lists all invoices owned by the current user.
    * Outstanding: lists all invoices owned by the current user, not paid and passed the due date.
    * Open: lists all invoices owned by the current user, not paid either passed the due date or not.
    * Open: lists all invoices owned by the current user, but have been paid.
    * To receive a payment, system should provide a list of unpaid(open) invoices to the user to select from.

In addition to the user management module.


___

## Database Structure
### Database Schema

```SQL
CREATE TABLE users (
id INTEGER NOT NULL PRIMARY KEY,
username TEXT NOT NULL,
hash TEXT NOT NULL);


CREATE TABLE properties (
id INTEGER NOT NULL PRIMARY KEY,
name TEXT NOT NULL,
rent INTEGER NOT NULL,
beds INTEGER NOT NULL,
description TEXT NOT NULL,
owner_id INTEGER NOT NULL,
image TEXT,
FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE contacts (
id INTEGER NOT NULL PRIMARY KEY,
name TEXT NOT NULL,
phone TEXT NOT NULL,
owner_id INTEGER NOT NULL,
FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE);


CREATE TABLE leases (
id INTEGER NOT NULL PRIMARY KEY,
start TEXT NOT NULL,
end TEXT NOT NULL,
property_id INTEGER NOT NULL,
contact_id INTEGER NOT NULL,
amount INTEGER NOT NULL,
owner_id INTEGER NOT NULL,
FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE);


CREATE TABLE invoices (
id INTEGER NOT NULL PRIMARY KEY,
amount float NOT NULL,
due_date TEXT NOT NULL,
lease_id INTEGER NOT NULL,
contact_id INTEGER NOT NULL,
property_id INTEGER NOT NULL,
owner_id INTEGER NOT NULL,
paid INTEGER NOT NULL,
FOREIGN KEY (lease_id) REFERENCES leases(id) ON DELETE CASCADE,
FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE);

```