create database journify_db;

use journify_db;

create table `user_booked_train_details` (
	`username` varchar(255) not null,
    `email` varchar(255) not null,
    `booking_id` int not null primary key auto_increment,
    `train_no` int not null,
    `train_name` varchar(255) not null,
    `origin` varchar(255) not null,
    `destination` varchar(255) not null,
    `day_of_week` varchar(255) not null,
    `travel_date` date not null,
    `Status` varchar(255) not null);

create table `user_booked_flight_details` (
	`username` varchar(255) not null,
    `email` varchar(255) not null,
    `booking_id` int not null primary key auto_increment,
    `flight_no` int not null,
    `airline` varchar(255) not null,
    `origin` varchar(255) not null,
    `destination` varchar(255) not null,
    `dep_time` time not null,
    `arr_time` time not null,
    `travel_date` date not null,
    `Status` varchar(255) not null);

create table airports (
  city varchar(255) not null,
  iata varchar(5) not null,
  icao varchar(5) not null);
  
create table users (
  username varchar(255) not null,
  password varchar(20) not null,
  email varchar(255) not null);
  
create table user_booked_flight_details (
  username varchar(255) not null,
  email varchar(255) not null,
  booking_id int not null auto_increment primary key,
  flight_no int not null,
  airline varchar(255) not null,
  origin varchar(255) not null,
  destination varchar(255) not null,
  dep_time time not null,
  arr_time time not null,
  travel_date date not null,
  Status varchar(255) not null);
  
create table user_booked_train_details (
  username varchar(255) not null,
  email varchar(255) not null,
  booking_id int not null auto_increment primary key,
  train_no int not null,
  train_name varchar(255) not null,
  origin varchar(255) not null,
  destination varchar(255) not null,
  day_of_week varchar(255) not null,
  travel_date date not null,
  Status varchar(255) not null);
  
