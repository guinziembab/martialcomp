# MartialComp Dashboards

## Introduction

This directory contains the complete documentation for the various dashboards available in the MartialComp application. Each user type has a dashboard specific to their role, offering features tailored to their needs.

## Dashboard Types

MartialComp offers several dashboards, each designed for a specific role:

1. [**Participant Dashboard**](./participants/README.md) - For martial arts practitioners who participate in competitions
2. [**Club Dashboard**](./clubs/README.md) - For club managers and their administrators
3. [**Federation Dashboard**](./federations/README.md) - For federation administrators
4. [**Referee/Judge Dashboard**](./referees/README.md) - For referees and judges who evaluate competitions
5. [**Multidiscipline Coach Dashboard**](./coaches/README.md) - For coaches who manage multiple disciplines
6. [**Combat Dashboard**](./combat/README.md) - Specialized interface for combat management

## Accessing Dashboards

Each user is automatically redirected to the dashboard corresponding to their role after logging in. The redirect is managed by the `dashboard` view in `competitions/views/dashboard/base.py`.

## Common Dashboard Structure

All dashboards share a common structure:

- **Header**: Displays the user's name, role, and provides access to settings and logout
- **Sidebar**: Navigation to the different sections of the dashboard
- **Main Content**: Displays information and features specific to each section
- **Footer**: Information about the application version and useful links

## Dashboard Customization

Users can customize certain aspects of their dashboard:
- Choice of widgets displayed on the home page
- Display order of information
- Notification preferences

## Common Features

All dashboards offer these basic features:
- Overview with key statistics
- Notifications and alerts
- User profile management
- Calendar of upcoming events
- Access to documentation

## Multilingual Support

All dashboards support multilingualism and are available in the following languages:
- French (fr) - Default language
- English (en)
- Spanish (es)
- Italian (it)
- German (de)
- Norwegian (no)
- Japanese (ja)
- Chinese (zh)
- Hindi (hi)
- Arabic (ar)
- Swahili (sw)
- Amharic (am)
- Zulu (zu)
- Yoruba (yo)
- Portuguese (pt)
- Korean (ko)

## Technical Design

The dashboards are implemented using:
- Django for the backend
- HTML/CSS/JavaScript for the frontend
- Bootstrap for responsive layout
- AJAX technology for dynamic updates

## Detailed Documentation

For more details on each dashboard, see the links above or explore the subdirectories of this directory.
