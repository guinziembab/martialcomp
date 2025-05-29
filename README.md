# MartialComp

MartialComp is a comprehensive web application for managing martial arts competitions, federations, clubs, and practitioners.

## Features

- **Federation Management**: Create and manage martial arts federations
- **Club Management**: Manage clubs, memberships, and affiliations
- **Practitioner Management**: Track practitioner information, grades, and competition history
- **Competition Organization**: 
  - Schedule and manage competitions
  - Create and manage competition categories
  - Handle participant registrations
  - Judge assignment and management
  - Scoring system for various competition types
- **Grade Management**: Comprehensive system for tracking and managing martial arts grades

## Technical Scoring System

MartialComp includes a unified technical scoring system for various martial arts performances:

- Support for multiple scoring methodologies (weighted average, point system, direct elimination)
- Customizable scoring criteria with weights
- Real-time judging capabilities
- Automated ranking generation
- Medal assignment and results management

For detailed documentation on the scoring system, see [docs/scoring_system.md](/docs/scoring_system.md).

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Create a superuser: `python manage.py createsuperuser`
5. Load initial data:
   - `python manage.py load_disciplines`
   - `python manage.py load_competition_types`
   - `python manage.py initialize_grade_systems`
6. Run the development server: `python manage.py runserver`

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file included in the repository.