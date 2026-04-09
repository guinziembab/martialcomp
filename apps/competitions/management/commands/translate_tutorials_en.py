"""
Management command to translate all 81 tutorials from French to English.
Updates title_en, steps_en, and tip_en fields via django-modeltranslation.

Usage: python manage.py translate_tutorials_en
"""
import json

from django.core.management.base import BaseCommand

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# =============================================================================
# TRANSLATION DATA
# Structure: {section_order: {title_en, tutorials: {number: {title_en, steps_en, tip_en}}}}
# =============================================================================

TRANSLATIONS = {
    # =========================================================================
    # Section 1: Onboarding & Getting Started (7 tutorials)
    # =========================================================================
    1: {
        'title_en': 'Onboarding & Getting Started',
        'tutorials': {
            1: {
                'title_en': 'Create your account and choose your role',
                'steps_en': [
                    "Access MartialComp : Go to martialcomp.com and click on 'Sign up for free'. You can also download the mobile app from the Play Store or App Store.",
                    "Fill in the registration form : Enter your last name, first name, email address and password. You can also sign up via Google, Facebook or Apple ID for simplified access.",
                    "Choose your main role : Select your role: Club Manager, Coach, Judge/Referee, Practitioner or Federation Manager. This choice determines your dashboard and features, but you can add other roles later.",
                    "Confirm your email : Check your inbox and click the confirmation link. Your account is now active and you can access your personalized dashboard.",
                ],
                'tip_en': 'You can hold multiple roles (e.g., coach AND practitioner). Switch between your roles from the side menu at any time.',
            },
            2: {
                'title_en': 'Create your club',
                'steps_en': [
                    "Launch the creation wizard : From your dashboard, click on 'Create a club'. The 4-step setup wizard starts automatically.",
                    "General information : Enter the club name, acronym, full address and contact details (phone, email, website). Add your logo in PNG or JPG format (recommended size: 500x500px).",
                    "Choose your disciplines : Select one or more disciplines from the 14+ available: Karate, Judo, BJJ, Taekwondo, MMA, Kung Fu, Aikido, Kendo, Muay Thai, Boxing, Capoeira, etc.",
                    "Customize your subdomain : Choose your unique address: your-club.martialcomp.com. This will be your club's public address, accessible to everyone.",
                    "Configure options : Set opening hours, add a description and photos of your dojo. Enable or disable online practitioner registration.",
                ],
                'tip_en': 'Your club is created with the Free plan (up to 10 members). All features are available from the start. Upgrade to Premium when you exceed 10 members.',
            },
            3: {
                'title_en': 'Create your federation',
                'steps_en': [
                    "Request creation : Select the 'Federation Manager' role during registration or add it from settings. Fill in the creation form with your federation's official information.",
                    "Official information : Enter the full name, acronym, country, covered disciplines, official registration number and contact details.",
                    "Configure the public site : Customize your public page: banner, logo, colors, description, photo gallery and links to your social media.",
                    "Define the structure : Configure your regional leagues if applicable, define affiliation categories for clubs and membership fee rates.",
                ],
                'tip_en': 'Federations benefit from an extended administration space to oversee all affiliated clubs, competitions and grades.',
            },
            4: {
                'title_en': 'Set up your coach profile',
                'steps_en': [
                    "Access the coach profile : From the side menu, click on 'My coach profile'. If you don't have the coach role yet, add it from Settings > My roles.",
                    "Enter your qualifications : Add your diplomas (BPJEPS, DEJEPS, CQP, etc.), your grades in each discipline, and your years of experience.",
                    "Define your disciplines : Select the disciplines you teach and your specialization level for each one (beginners, advanced, competition).",
                    "Set your availability : Indicate your weekly teaching slots. This information will be visible to clubs looking for coaches.",
                ],
                'tip_en': 'A complete coach profile with photo and certifications significantly increases your visibility among clubs.',
            },
            5: {
                'title_en': 'Set up your judge profile',
                'steps_en': [
                    "Activate the judge role : From Settings > My roles, activate the 'Judge / Referee' role. Enter your judge license number if applicable.",
                    "Add your qualifications : Indicate your judge level (regional, national, international), the disciplines you are qualified for, and your certifications.",
                    "Define your specialties : Kata/techniques, combat, artistic scoring... Each specialty makes you eligible for corresponding competitions.",
                    "Enter your availability : Indicate your geographic zones and availability periods for competitions.",
                ],
                'tip_en': 'Competition organizers will be able to search for and invite you directly based on your qualifications and availability.',
            },
            6: {
                'title_en': 'Set up your practitioner profile',
                'steps_en': [
                    "Complete personal information : Enter your date of birth, gender, weight (for competition categories), height and profile photo.",
                    "Add your current grade : Indicate your main discipline, your current grade (belt), the date obtained and the issuing organization.",
                    "Enter your license : Add your federation license number, expiration date and current valid medical certificate.",
                    "Emergency contacts : Add at least one emergency contact (required for competitions): name, phone number, relationship.",
                ],
                'tip_en': 'A complete profile is required to register for competitions. Weight and grade automatically determine your category.',
            },
            7: {
                'title_en': 'Understand the dashboard and navigation',
                'steps_en': [
                    "The dashboard : Your dashboard displays a personalized summary: upcoming events, recent messages, quick statistics and shortcuts to your frequent actions.",
                    "The sidebar : The side menu gives access to all sections: Members, Competitions, Grades, Finances, Calendar, Settings. It adapts to your active role.",
                    "Switch roles : If you have multiple roles (e.g., coach + practitioner), click on your avatar in the top right to switch. The dashboard and menu adapt automatically.",
                    "Notifications and messages : The bell icon in the top right shows your notifications: registrations, results, messages. Configure your notification preferences in settings.",
                    "Global search : Use the search bar to quickly find a practitioner, club, competition or event.",
                ],
                'tip_en': 'Customize your dashboard by pinning your favorite widgets. The keyboard shortcut Ctrl+K opens the quick search.',
            },
        },
    },

    # =========================================================================
    # Section 2: Club Management (10 tutorials)
    # =========================================================================
    2: {
        'title_en': 'Club Management',
        'tutorials': {
            1: {
                'title_en': 'Add practitioners manually',
                'steps_en': [
                    "Open the add form : From Members > Add a practitioner, fill in the form: last name, first name, date of birth, gender, email and phone.",
                    "Additional information : Add the current grade, license number, ID photo (optional) and medical certificate.",
                    "Assign to a group : Assign the practitioner to one or more training groups (e.g., Adult Advanced Karate, Children Beginner Judo).",
                    "Send the invitation : Check 'Send an email invitation' so the practitioner can create their own account and access their online profile.",
                ],
                'tip_en': 'The practitioner will receive an email with a link to complete their registration and download the mobile app.',
            },
            2: {
                'title_en': 'Bulk import practitioners (CSV/Excel)',
                'steps_en': [
                    "Download the template : From Members > Import, download the CSV or Excel template. The file contains required columns: Last Name, First Name, Date_of_birth, Email, and optional columns: Grade, License, Phone.",
                    "Fill in the file : Complete the file with your practitioners' data. Follow the formats: dates in DD/MM/YYYY, grades as text (e.g., 'Green belt', '2nd Dan').",
                    "Upload and map columns : Import the file. The mapping interface lets you associate each column of your file with MartialComp fields. Verify the mapping.",
                    "Validate and correct : MartialComp detects errors (duplicates, invalid formats). Fix the error rows or skip them. Confirm the import.",
                ],
                'tip_en': 'You can import up to 500 practitioners in a single operation. The import automatically detects duplicates by email or last name + first name + date of birth.',
            },
            3: {
                'title_en': 'Manage practitioner records',
                'steps_en': [
                    "Access the record : From the members list, click on a practitioner's name to open their complete record.",
                    "View details : The record displays: personal information, grade history, competitions entered, attendance, and membership fees.",
                    "Edit information : Click 'Edit' to update data. Changes are tracked in the history.",
                    "Quick actions : From the record, you can: register for a competition, assign a grade, send a message, generate a certificate.",
                ],
                'tip_en': 'Use advanced filters (grade, age, valid license, paid membership) to quickly find a practitioner.',
            },
            4: {
                'title_en': 'Create a user account for a practitioner',
                'steps_en': [
                    "Access the practitioner record : Open the record of the relevant practitioner from the members list.",
                    "Link to an account : Click 'Create a user account'. An invitation email will be sent to the practitioner with a password creation link.",
                    "Set permissions : Choose what the practitioner can do: view their results, register for competitions, see the calendar, pay online.",
                ],
                'tip_en': 'Minor practitioners can have an account linked to a parent\'s account via the Family Group feature.',
            },
            5: {
                'title_en': 'Manage club roles and permissions',
                'steps_en': [
                    "Access role management : From Settings > Roles and permissions, view available roles: Administrator, Secretary, Treasurer, Coach, Member.",
                    "Assign a role : Select a member and assign them a role. Each role grants access to specific features.",
                    "Customize permissions : For each role, define the rights: read-only, edit, delete, access to finances, registration management.",
                    "Audit access : View the activity log to see who did what and when in the club administration.",
                ],
                'tip_en': 'The Administrator role has all rights. Create a Secretary role with access to members and calendar but not finances.',
            },
            6: {
                'title_en': 'Track attendance / Check-in',
                'steps_en': [
                    "Create a session : From Attendance > New session, select the training group, date and class time.",
                    "Check in by list : Display the group members list and check off those present. Check-in is done with a single tap on mobile.",
                    "Check in by QR code : Display the session QR code. Practitioners scan it with their phone when arriving at the dojo.",
                    "View statistics : Visualize attendance rates by practitioner, group and period. Identify repeated absences.",
                ],
                'tip_en': 'QR code check-in is the fastest method for large groups. The code refreshes each session to prevent cheating.',
            },
            7: {
                'title_en': 'Manage training programs',
                'steps_en': [
                    "Create a program : From Programs > New, define the name, discipline, level (beginner, intermediate, advanced) and cycle duration.",
                    "Schedule sessions : Add weekly slots: day, start time, end time, room/tatami, responsible coach.",
                    "Define content : For each session, add a plan: warm-up, technical work, sparring/randori, cool-down. Attach files or videos.",
                    "Publish and notify : Publish the program. Group practitioners receive a notification with the complete schedule.",
                ],
                'tip_en': 'Duplicate an existing program to quickly create a new cycle with variations.',
            },
            8: {
                'title_en': 'Generate and use club QR codes',
                'steps_en': [
                    "Generate the club QR code : From Settings > QR Codes, generate your club's QR code. It allows visitors to directly access your public page.",
                    "Special QR codes : Generate QR codes for: online registration, session check-in, event page, or mobile app link.",
                    "Print and display : Download QR codes in high resolution for printing. Available formats: PNG, SVG, PDF (A4 or business card).",
                    "Track statistics : View the number of scans per QR code, per day and per type. Identify the most effective QR codes.",
                ],
                'tip_en': 'Display the registration QR code at the entrance of your dojo. Every scan is a potential customer!',
            },
            9: {
                'title_en': 'Request federation affiliation',
                'steps_en': [
                    "Find your federation : From Club > Affiliation, search for your federation by name, discipline or country.",
                    "Submit the request : Fill in the affiliation form: club information, registration number, supporting documents (bylaws, insurance, etc.).",
                    "Track the status : Your request goes through stages: Submitted > Under review > Approved/Rejected. You receive notifications at each step.",
                    "Renew each season : Affiliation is seasonal. An automatic reminder is sent 30 days before expiration.",
                ],
                'tip_en': 'Affiliation gives you access to the federation\'s official competitions and centralized license management.',
            },
            10: {
                'title_en': 'Manage practitioner transfers',
                'steps_en': [
                    "Initiate a transfer : From a practitioner's record, click 'Request a transfer'. Select the destination club and the reason for transfer.",
                    "Validation process : The destination club receives the request and can accept or reject it. If a federation is involved, it must also validate.",
                    "Effective transfer : Once validated, the practitioner is automatically transferred with their grade and competition history.",
                    "View history : The transfer history is visible on the practitioner's record and in club reports.",
                ],
                'tip_en': 'Some federations impose transfer periods (transfer windows). MartialComp automatically respects these rules.',
            },
        },
    },

    # =========================================================================
    # Section 3: Competitions - Creation & Setup (6 tutorials)
    # =========================================================================
    3: {
        'title_en': 'Competitions - Creation & Setup',
        'tutorials': {
            1: {
                'title_en': 'Create an individual competition',
                'steps_en': [
                    "Launch creation : From Competitions > Create, choose the 'Individual' type. Enter the name, discipline(s), dates and venue.",
                    "Define the format : Choose the format: Combat (kumite, randori, sparring), Technical (kata, poomsae, forms), or Mixed (both).",
                    "Configure categories : Define categories by gender, age range, weight and/or grade. MartialComp offers standard category templates by discipline.",
                    "Options and publication : Enable desired options: online registration, payment, live streaming, public results. Publish the competition.",
                ],
                'tip_en': 'Use category templates (WKF, IJF, ITF...) to save time. You can customize them after creation.',
            },
            2: {
                'title_en': 'Create a team competition (Synchro/Song Luyen)',
                'steps_en': [
                    "Choose team mode : During creation, select the 'Team' type. Define the minimum and maximum number of members per team.",
                    "Configure team format : Choose the format: Synchronization (team kata/poomsae), Song Luyen (pre-arranged combat for two), or Team Combat (relay).",
                    "Define composition : Specify roles within the team: number of starters, number of substitutes, whether mixed compositions are allowed or not.",
                    "Team scoring criteria : For technical scoring, define whether judges score the team as a whole or each member individually.",
                ],
                'tip_en': 'Synchro mode allows scoring with specific synchronization criteria (timing, alignment, shared expression).',
            },
            3: {
                'title_en': 'Configure competition categories',
                'steps_en': [
                    "Access category management : From the created competition, go to the Categories tab. Click 'Add a category'.",
                    "Define criteria : For each category, define: gender (M/F/Mixed), age range (e.g., 12-14 years), weight range (e.g., -60kg), minimum/maximum grade.",
                    "Name the category : Give a clear name: 'Cadet Male -52kg' or 'Kata Adult Female Advanced'. MartialComp generates automatic names if you prefer.",
                    "Order categories : Reorder categories by drag-and-drop to set the order of appearance on competition day.",
                ],
                'tip_en': 'Import categories from a previous competition to save time. Use the \'Smart Duplication\' option to create variants.',
            },
            4: {
                'title_en': 'Duplicate an existing competition',
                'steps_en': [
                    "Find the source competition : From Competitions > History, find the competition you want to duplicate.",
                    "Launch duplication : Click the 3 dots > Duplicate. Choose what to copy: categories, rules, settings, pricing.",
                    "Adjust settings : Modify dates, venue and any necessary parameters. Categories and rules are copied identically.",
                ],
                'tip_en': 'Ideal for recurring annual competitions. Duplicate the previous edition and simply update the dates.',
            },
            5: {
                'title_en': 'Configure visibility options',
                'steps_en': [
                    "Access visibility settings : From the competition, go to Settings > Visibility and sharing.",
                    "Online registration : Enable/disable public registration. Set the opening and closing dates for registrations.",
                    "Results and rankings : Choose whether results are public in real-time, published after validation, or private (organizer only).",
                    "Live streaming : Enable streaming mode and add the YouTube/Twitch/Facebook Live link for display on the public page.",
                ],
                'tip_en': 'Live results attract spectators to your page and increase visibility for your club or federation.',
            },
            6: {
                'title_en': 'Configure combat rules',
                'steps_en': [
                    "Choose a ruleset : Select a pre-configured ruleset (WKF, IJF, ITF, IBJJF, etc.) or create a custom one.",
                    "Define scoring : Configure actions and their points: Yuko (1pt), Waza-ari (2pts), Ippon (3pts), etc. Add penalties (Shido, Hansoku, etc.).",
                    "Configure rounds : Define round duration, number of rounds, breaks, and victory conditions (points, Ippon, forfeit).",
                    "Special rules : Configure specific rules: Golden Score (overtime), Hantei (judges' decision), early finish by point gap.",
                ],
                'tip_en': 'Save your custom rulesets as templates to reuse them in future competitions.',
            },
        },
    },

    # =========================================================================
    # Section 4: Registrations & Teams (7 tutorials)
    # =========================================================================
    4: {
        'title_en': 'Registrations & Teams',
        'tutorials': {
            1: {
                'title_en': 'Register practitioners for a competition',
                'steps_en': [
                    "Find the competition : From Competitions > Open for registration, find the desired competition and click 'Register'.",
                    "Select practitioners : Your members list is displayed. Select one or more practitioners. MartialComp automatically indicates eligible categories for each one.",
                    "Confirm categories : For each practitioner, confirm or change the proposed category. The system verifies that weight, age and grade match.",
                    "Validate and pay : Confirm registrations. If the competition requires payment, proceed with payment for all registrations.",
                ],
                'tip_en': 'Practitioners with an incomplete profile (missing weight, expired license) will be flagged with a red alert.',
            },
            2: {
                'title_en': 'Bulk registration via form',
                'steps_en': [
                    "Access bulk mode : From the registration screen, click 'Bulk registration'. Select the target category.",
                    "Select the group : Filter by training group, grade or age. Check eligible practitioners in one click.",
                    "Verify and adjust : The verification screen shows each practitioner with their category. Correct any errors.",
                    "Confirm the batch : Validate all registrations in a single operation. A summary is sent by email.",
                ],
                'tip_en': 'Bulk registration is ideal for clubs registering 10+ practitioners for the same competition.',
            },
            3: {
                'title_en': 'Create and manage teams',
                'steps_en': [
                    "Create a team : From the competition, click 'Register a team'. Name the team and select the category.",
                    "Add members : Add team members from your practitioners list. Respect the defined minimum and maximum numbers.",
                    "Set starters and substitutes : Designate starters and substitutes by drag-and-drop. The order of appearance can be set here.",
                    "Validate the team : Verify team compliance (number of members, individual categories) and confirm registration.",
                ],
                'tip_en': 'In team competitions, the team name appears on display boards and official results.',
            },
            4: {
                'title_en': 'Change a team\'s category',
                'steps_en': [
                    "Access the team : From your registrations, find the team to modify and click 'Edit'.",
                    "Change the category : Select the new category from the dropdown menu. The system verifies that the team meets the criteria.",
                    "Confirm the change : Validate. If the competition has different registration fees per category, the adjustment is automatic.",
                ],
                'tip_en': 'Category change is only possible while registrations are still open.',
            },
            5: {
                'title_en': 'Request a partnership (inter-club merger)',
                'steps_en': [
                    "Identify the need : Your club doesn't have enough members to form a complete team? A partnership allows merging teams from different clubs.",
                    "Create the partnership request : From the incomplete team, click 'Propose a partnership'. Select the partner club and the positions to fill.",
                    "Send the proposal : The partner club receives the request with details: competition, category, available positions, conditions.",
                    "Finalize the partnership : Once accepted, the merged team appears with members from both clubs. The team bears a name combining both clubs.",
                ],
                'tip_en': 'The partnership is subject to approval by the competition organizer and, where applicable, the federation.',
            },
            6: {
                'title_en': 'Accept/reject a partnership request',
                'steps_en': [
                    "Receive the notification : You receive a partnership request notification. Click on it to see the details.",
                    "Review the proposal : Check: the requesting club, the competition, the category, the positions to fill and the proposed conditions.",
                    "Accept or reject : Click 'Accept' to validate the partnership and select your members, or 'Reject' with an explanatory message.",
                ],
                'tip_en': 'You can propose a counter-offer by modifying the conditions before accepting.',
            },
            7: {
                'title_en': 'Manage received registrations (approval)',
                'steps_en': [
                    "Access the registrations panel : From the competition, go to the Registrations tab. View registrations by status: Pending, Approved, Rejected.",
                    "Review and approve : Click on a registration to verify the practitioner's information. Approve individually or in batch.",
                    "Reject with reason : In case of rejection, select a reason: incorrect category, invalid license, late registration, etc.",
                    "Export the list : Export the list of valid registrants in CSV or PDF for weigh-in and management on the day.",
                ],
                'tip_en': 'Enable automatic approval if you don\'t want to manually validate each registration.',
            },
        },
    },

    # =========================================================================
    # Section 5: Competition Day - Combat (8 tutorials)
    # =========================================================================
    5: {
        'title_en': 'Competition Day - Combat',
        'tutorials': {
            1: {
                'title_en': 'Generate pools automatically',
                'steps_en': [
                    "Access pool management : From the competition, go to Pools > Generate automatically. Select the categories to process.",
                    "Configure distribution : Define: number of competitors per pool, separation of same-club members, manual seeding (optional).",
                    "Generate and verify : Click 'Generate'. MartialComp distributes competitors while avoiding intra-club matchups in the first round.",
                    "Adjust manually : If needed, move competitors between pools by drag-and-drop. The system checks for conflicts in real time.",
                ],
                'tip_en': 'The distribution algorithm ensures fairness by separating clubs and balancing skill levels across pools.',
            },
            2: {
                'title_en': 'Organize and reorganize pools',
                'steps_en': [
                    "Pool overview : The pools screen shows all categories with the number of competitors, pools and status (draft, validated, in progress).",
                    "Edit a pool : Click on a pool to see the competitors. Use drag-and-drop to move a competitor to another pool.",
                    "Manage absences : Mark a competitor as absent or withdrawn. The system automatically recalculates matchups and rankings.",
                    "Validate pools : Once satisfied, validate the pools. This action automatically generates the matchup table.",
                ],
                'tip_en': 'Validate pools category by category to start fights for the first categories while you finalize the others.',
            },
            3: {
                'title_en': 'Schedule the fight calendar',
                'steps_en': [
                    "Define combat areas : From Schedule > Areas, define the number of available tatamis/rings and their names (Tatami 1, Ring A, etc.).",
                    "Assign time slots : Drag categories onto areas and time slots. MartialComp calculates the estimated duration automatically.",
                    "Detect conflicts : The system detects conflicts: a competitor registered in 2 categories at the same time. Use alerts to adjust.",
                    "Publish the schedule : Publish the schedule. Competitors, coaches and judges receive a notification with their appearance times.",
                ],
                'tip_en': 'Plan for 20% extra time per category to handle inevitable delays.',
            },
            4: {
                'title_en': 'Use the combat interface (live scoring)',
                'steps_en': [
                    "Connect to the area : On your tablet or phone, open MartialComp and select your assigned combat area. Enter your judge PIN.",
                    "The scoring interface : The screen displays: the 2 competitors (red/blue), action buttons (points, penalties), the timer and current score.",
                    "Award points : Press the scoring buttons: Yuko (+1), Waza-ari (+2), Ippon (+3) for the red or blue competitor. Points display in real time.",
                    "Manage penalties : Press Penalty to award a warning (Shido) or disqualification (Hansoku). Penalties are cumulative.",
                    "End the fight : The timer stops automatically. Validate the result (victory by points, Ippon, forfeit). The ranking updates instantly.",
                ],
                'tip_en': 'The interface is optimized for tablets in landscape mode. Buttons are intentionally large for fast, error-free use.',
            },
            5: {
                'title_en': 'Multi-tatami Kiosk mode',
                'steps_en': [
                    "Activate Kiosk mode : From Settings > Kiosk Mode, enable the mode and set a PIN code for each combat area.",
                    "Configure each tablet : On each area tablet, log in and select the corresponding area. Enter the PIN to lock the screen to this area.",
                    "Independent management : Each area operates autonomously: scoring, timer, display. The central scoreboard updates in real time.",
                    "Spectator display screen : Connect an additional screen in 'Spectator' mode to show the score in large format, visible from the stands.",
                ],
                'tip_en': 'Kiosk mode prevents judges from accidentally navigating away from the scoring interface.',
            },
            6: {
                'title_en': 'Follow live rankings',
                'steps_en': [
                    "Live dashboard : The tracking screen shows in real time: ongoing fights by area, pool rankings, progression toward final rounds.",
                    "Filter by category : Select a category to see the details: completed, in-progress and upcoming pools, with provisional rankings.",
                    "Automatic notifications : The system automatically notifies coaches when their competitors need to report to the combat area.",
                ],
                'tip_en': 'Display the dashboard on a large screen in the reception area so all participants can follow the progress.',
            },
            7: {
                'title_en': 'Generate final rounds (semi-finals/finals)',
                'steps_en': [
                    "Pools completed : Once all pools in a category are completed, the system calculates qualifiers according to defined rules (1st and 2nd per pool, etc.).",
                    "Generate the bracket : Click 'Generate final rounds'. The elimination bracket (quarterfinals, semis, final, bronze match) is generated automatically.",
                    "Manage repechage : If the rules provide for it, repechage rounds are automatically generated with the semi-final losers.",
                    "Launch the finals : Final round fights appear in the schedule. Scoring works the same way as for pools.",
                ],
                'tip_en': 'The bracket (elimination table) is automatically generated while avoiding matchups between competitors from the same club when possible.',
            },
            8: {
                'title_en': 'Manage the podium ceremony',
                'steps_en': [
                    "Access the podium : From the completed category, click 'Podium'. The final ranking is displayed: Gold, Silver, Bronze (and possibly 2 bronzes).",
                    "Progressive display : Use the 'Ceremony' mode for progressive display: 3rd, then 2nd, then 1st, with animations and sound effects.",
                    "Project on large screen : Connect Presentation mode to a projector for a spectacular display during the medal ceremony.",
                    "Share results : Podiums are automatically published on the competition page and can be shared on social media.",
                ],
                'tip_en': 'Take a photo of the podium and add it to the competition to enrich the gallery and social media.',
            },
        },
    },

    # =========================================================================
    # Section 6: Technical Scoring (6 tutorials)
    # =========================================================================
    6: {
        'title_en': 'Technical Scoring',
        'tutorials': {
            1: {
                'title_en': 'Configure scoring criteria',
                'steps_en': [
                    "Access criteria : From the competition, go to Scoring > Criteria. Select a template or create your own criteria.",
                    "Define criteria : Add scoring criteria: Technique (positions, transitions), Power (kime, dynamics), Rhythm (tempo, fluidity), Expression (zanshin, spirit).",
                    "Assign weights : Define the weight of each criterion: e.g., Technique 40%, Power 25%, Rhythm 20%, Expression 15%. The total must equal 100%.",
                    "Define the scale : Choose the scoring scale: 1-5, 1-10, 5.0-10.0, or custom. Define the increment (0.1, 0.5 or 1).",
                ],
                'tip_en': 'WKF and WTF templates are pre-configured. Customize them to your specific needs.',
            },
            2: {
                'title_en': 'Assign judges to categories',
                'steps_en': [
                    "Open the assignment panel : From Scoring > Judges, view the list of registered judges and the categories to cover.",
                    "Assign by category : Drag judges to categories. Define the number of judges per category (usually 5 or 7).",
                    "Neutrality check : MartialComp automatically checks for conflicts of interest: a judge cannot score a competitor from their own club.",
                    "Manage rotations : Plan judge rotations between categories to prevent fatigue and maintain fairness.",
                ],
                'tip_en': 'The bias detection system analyzes scoring gaps between judges and alerts if a judge consistently scores too high or too low.',
            },
            3: {
                'title_en': 'Use the technical scoring sheet',
                'steps_en': [
                    "Log in as a judge : On your tablet, log in with your judge account. Select the assigned category.",
                    "Scoring interface : The screen displays the current competitor, scoring criteria and numeric keypad. Each criterion has its own slider or pad.",
                    "Score by round : For each competitor, enter your score for each criterion. Validate your scoring before moving to the next one.",
                    "Save : Your scoring is saved instantly. You can modify your scores as long as the round has not been locked by the organizer.",
                ],
                'tip_en': 'The digital interface is optimized for fast input on tablets. A single tap for each score.',
            },
            4: {
                'title_en': 'Team technical scoring (Synchro)',
                'steps_en': [
                    "Understand team mode : In Synchro scoring, additional criteria appear: Synchronization, Spatial Alignment, Shared Expression.",
                    "Score the team as a whole : If configured this way, score the team as a whole for each criterion, including synchronization.",
                    "Score individually + team : If configured for mixed scoring, score each member individually THEN add a team score for synchronization.",
                ],
                'tip_en': 'In Synchro mode, the synchronization criterion typically accounts for 20-30% of the total score.',
            },
            5: {
                'title_en': 'Lock and publish scores',
                'steps_en': [
                    "Verify scores : From the organizer panel, view all judges\' scores for each competitor. Identify suspicious gaps.",
                    "Lock a round : Click 'Lock' to prevent any modifications. The final calculation (remove highest/lowest score, average) is performed.",
                    "Publish results : Publish the rankings. Detailed scores by judge can be hidden or visible depending on your configuration.",
                    "Test mode / reset : Before the competition, use test mode to verify the system. Reset deletes all test scores.",
                ],
                'tip_en': 'Round-by-round locking allows publishing results round by round while the competition continues.',
            },
            6: {
                'title_en': 'View provisional rankings',
                'steps_en': [
                    "Access rankings : From the Rankings tab, view real-time rankings with scores by criterion and the final score.",
                    "Sort and filter : Sort by total score or by specific criterion. Filter by pool or all competitors.",
                    "Judge statistics : View statistics: average per judge, standard deviation, bias detection. An essential tool for fairness.",
                ],
                'tip_en': 'The provisional ranking is only visible to organizers and judges. It is published to competitors only after locking.',
            },
        },
    },

    # =========================================================================
    # Section 7: Results & Rankings (4 tutorials)
    # =========================================================================
    7: {
        'title_en': 'Results & Rankings',
        'tutorials': {
            1: {
                'title_en': 'View competition results',
                'steps_en': [
                    "Find the competition : From the Competitions menu or the public page, select the desired competition.",
                    "Browse results : Results are organized by category. For each category: podium, complete ranking, and score details.",
                    "Fight details : Click on a fight to see the details: score per round, penalties, timer, and possibly the fight video.",
                ],
                'tip_en': 'Public results are accessible without a MartialComp account via the competition link.',
            },
            2: {
                'title_en': 'Publish and share results',
                'steps_en': [
                    "Validate results : From the organizer panel, review each category's results. Click 'Validate and publish'.",
                    "Generate the public link : A permanent link is generated for the results page. Copy it to share.",
                    "Share on social media : Use the built-in sharing buttons to publish on Facebook, Instagram, Twitter. Podiums automatically generate an image.",
                    "Results QR code : Generate a results QR code to display at the competition venue for spectators.",
                ],
                'tip_en': 'The automatic podium image is formatted for Instagram Stories (9:16) and Facebook (16:9).',
            },
            3: {
                'title_en': 'Export results (CSV/PDF)',
                'steps_en': [
                    "Access export : From Results > Export, choose the format: CSV (raw data), PDF (formatted report), or Excel.",
                    "Choose content : Select: General ranking, Podiums only, Detail by category, Medal report by club, or All.",
                    "Customize PDF : For PDF, choose the template: official report (with federation logo), simple report, or diplomas.",
                ],
                'tip_en': 'The medal report by club is particularly useful for federations and sponsors.',
            },
            4: {
                'title_en': 'View your personal track record',
                'steps_en': [
                    "Access My track record : From your practitioner profile, click 'Track Record'. Your competition history is displayed.",
                    "View statistics : Check: number of competitions, medals (gold/silver/bronze), win rate, progression over time.",
                    "Share your track record : Generate a public link to your track record or export it as PDF for your application or sponsorship files.",
                ],
                'tip_en': 'Your track record updates automatically after each competition. It is visible on your public profile if you allow it.',
            },
        },
    },

    # =========================================================================
    # Section 8: Grade Management (5 tutorials)
    # =========================================================================
    8: {
        'title_en': 'Grade Management',
        'tutorials': {
            1: {
                'title_en': 'Configure the grade system',
                'steps_en': [
                    "Access configuration : From Settings > Grades, select the discipline and define your grade system.",
                    "Create levels : Add levels in order: White belt, Yellow, Orange, Green, Blue, Brown, Black 1st Dan, 2nd Dan, etc.",
                    "Define prerequisites : For each grade, define: minimum time at previous grade, minimum age, minimum number of classes, whether an exam is required.",
                    "Assign colors : Assign belt colors for visual display in the interface and profiles.",
                ],
                'tip_en': 'Standard grade systems (Judo, Karate, TKD, BJJ) are pre-configured. You can customize them or create new ones.',
            },
            2: {
                'title_en': 'Assign a grade to a practitioner',
                'steps_en': [
                    "Access the record : From the practitioner's record, click on the Grades tab then 'Assign a new grade'.",
                    "Select the grade : Choose the grade from the list. The system automatically checks prerequisites (time, age, exams).",
                    "Enter details : Add the date of assignment, location, jury/examiner, and any observations.",
                    "Bulk assignment : From Grades > Bulk assignment, select multiple practitioners and assign the same grade to all.",
                ],
                'tip_en': 'A congratulatory email is automatically sent to the practitioner with their new grade.',
            },
            3: {
                'title_en': 'Organize a grade examination',
                'steps_en': [
                    "Create the exam : From Grades > Exams, create a new exam: date, location, discipline, covered grades, jury.",
                    "Register candidates : Add candidates manually or allow self-registration. The system checks each one's prerequisites.",
                    "On exam day : Use the exam interface to score each candidate: required techniques, sparring, theory.",
                    "Publish results : Validate passes and fails. Grades are automatically assigned to successful candidates.",
                ],
                'tip_en': 'Grade exams can be linked to a competition (e.g., grade promotion during a tournament).',
            },
            4: {
                'title_en': 'Manage grade history and progression',
                'steps_en': [
                    "View history : Each practitioner's record displays the complete grade history: date, location, jury, observations.",
                    "Visualize progression : A chart shows progression over time. Compare with the club average.",
                    "Revoke a grade : In case of error, revoke a grade with a reason. The history retains the revocation record.",
                ],
                'tip_en': 'Grade history is transferable if the practitioner changes clubs.',
            },
            5: {
                'title_en': 'Generate grade certificates',
                'steps_en': [
                    "Access certificates : From Grades > Certificates, select the practitioner and the grade for which to generate a certificate.",
                    "Choose the template : Select a certificate template: official (with federation logo), club, or custom.",
                    "Customize : Add signatures, club stamp and any special mentions. The verification QR code is added automatically.",
                    "Generate and distribute : Generate the PDF. Print or send by email. The QR code allows anyone to verify the certificate's authenticity.",
                ],
                'tip_en': 'The verification QR code links to a public MartialComp page that confirms the grade\'s validity.',
            },
        },
    },

    # =========================================================================
    # Section 9: Federation Management (8 tutorials)
    # =========================================================================
    9: {
        'title_en': 'Federation Management',
        'tutorials': {
            1: {
                'title_en': 'Manage affiliated clubs',
                'steps_en': [
                    "Overview : The federation dashboard displays the map of affiliated clubs, their status (active, pending, expired) and statistics.",
                    "Process requests : New affiliation requests appear in Clubs > Pending. Review documents and approve or reject.",
                    "Track renewals : View affiliations approaching expiration. Send automatic reminders 30, 15 and 7 days before.",
                ],
                'tip_en': 'The federation dashboard provides a real-time view of the total number of licensed practitioners across all clubs.',
            },
            2: {
                'title_en': 'Manage seasons and membership fees',
                'steps_en': [
                    "Create a season : From Seasons > New, define the start and end dates, and membership fee rates by type (club, individual, junior, senior).",
                    "Configure membership fees : Define amounts by category: club affiliation (fixed), individual license (per practitioner), insurance (optional).",
                    "Track payments : View received, pending and overdue fees in real time. Send automatic reminders.",
                    "Close the season : At the end of the season, close it to generate the financial report and prepare the next season.",
                ],
                'tip_en': 'Fees can be paid online via Stripe or by bank transfer. Tracking is automatic in both cases.',
            },
            3: {
                'title_en': 'Oversee competitions',
                'steps_en': [
                    "Global view : The federation calendar displays all competitions from affiliated clubs, with status and number of participants.",
                    "Sanction a competition : Clubs submit their competitions for sanctioning. Verify the rules, judges and validate.",
                    "View results : Access results from all sanctioned competitions. National rankings update automatically.",
                ],
                'tip_en': 'Competitions sanctioned by the federation are featured in the directory and public calendar.',
            },
            4: {
                'title_en': 'Manage judges and their qualifications',
                'steps_en': [
                    "Judge database : View the database of affiliated judges with their qualifications, specialties and activity history.",
                    "Manage levels : Assign qualification levels: regional, national, international. Define promotion criteria.",
                    "Neutrality tracking : MartialComp analyzes the scoring statistics of each judge and detects potential biases.",
                ],
                'tip_en': 'Judges with a balanced scoring history are highlighted for important competitions.',
            },
            5: {
                'title_en': 'Manage certifications',
                'steps_en': [
                    "Create a template : Design your certificate templates with the federation logo, legal mentions and dynamic fields.",
                    "Issue certificates : Generate certificates for: grades, judge qualifications, teaching diplomas, various attestations.",
                    "Public verification : Each certificate has a unique QR code. Anyone can scan it to verify authenticity on martialcomp.com.",
                ],
                'tip_en': 'Digital certificates are tamper-proof thanks to the verification QR code linked to MartialComp.',
            },
            6: {
                'title_en': 'Customize the federation public site',
                'steps_en': [
                    "Access the site builder : From Settings > Public site, open the page editor. Your federation has a URL: federation.martialcomp.com.",
                    "Customize appearance : Choose colors, theme, banner and logo. Add a description and your social media links.",
                    "Add content : Publish news, photo galleries, videos, competition calendar and downloadable documents.",
                    "Manage pages : Create additional pages: History, Leadership Team, Regulations, Contact.",
                ],
                'tip_en': 'The public site is optimized for SEO. The more complete it is, the better it will rank on Google.',
            },
            7: {
                'title_en': 'View statistics and reports',
                'steps_en': [
                    "Analytics dashboard : The dashboard displays KPIs: number of clubs, practitioners, competitions, active licenses, growth.",
                    "Reports by club : Generate detailed reports by club: number of members, fees, competition participation, grades awarded.",
                    "Reports by discipline : Analyze distribution by discipline, age, gender. Identify growth trends.",
                    "Export and share : Export reports in PDF, Excel or CSV for your general assemblies and official reports.",
                ],
                'tip_en': 'Reports are updated in real time. Schedule automatic monthly or quarterly deliveries.',
            },
            8: {
                'title_en': 'Manage training programs',
                'steps_en': [
                    "Create a program : From Training > New, define the program: title, discipline, level, duration, prerequisites.",
                    "Schedule sessions : Add training sessions: dates, venues, trainers, number of seats.",
                    "Manage registrations : Coaches and judges register online. Validate registrations and send convocations.",
                    "Tracking and certification : Track attendance at sessions. Issue certifications to participants who completed the program.",
                ],
                'tip_en': 'Completed training programs automatically appear on coaches\' and judges\' profiles.',
            },
        },
    },

    # =========================================================================
    # Section 10: Finances (5 tutorials)
    # =========================================================================
    10: {
        'title_en': 'Finances',
        'tutorials': {
            1: {
                'title_en': 'Track club transactions',
                'steps_en': [
                    "Overview : The financial dashboard displays: balance, month's revenue, expenses, and trend chart.",
                    "Record a transaction : Add income or expense: amount, date, category (membership fees, equipment, rental), description.",
                    "Automatic categorization : MartialComp automatically categorizes recurring transactions. Customize categories to your needs.",
                ],
                'tip_en': 'Connect your bank account to automatically import transactions and simplify reconciliation.',
            },
            2: {
                'title_en': 'Create and send invoices',
                'steps_en': [
                    "Create an invoice : From Finances > Invoices > New, select the recipient (practitioner, club, sponsor) and billing lines.",
                    "Customize : Add your logo, legal notices, payment terms. Choose the currency and VAT rate.",
                    "Send : Send the invoice by email. The recipient receives an online payment link (Stripe) and the invoice in PDF.",
                    "Track payments : View paid, pending and overdue invoices. Send automatic reminders.",
                ],
                'tip_en': 'Practitioner membership fees automatically generate invoices if you enable this option.',
            },
            3: {
                'title_en': 'Manage online payments (Stripe)',
                'steps_en': [
                    "Connect Stripe : From Settings > Payments, click 'Connect Stripe'. Follow the steps to link your Stripe account.",
                    "Configure checkout : Set rates for: membership fees, competition registrations, shop. Enable recurring payments if needed.",
                    "Test payment : Use Stripe's test mode to verify everything works before activating real payments.",
                    "Track revenue : The Stripe dashboard in MartialComp shows received payments, refunds and transfers to your bank account.",
                ],
                'tip_en': 'Stripe charges a fee of 1.4% + 0.25 EUR per transaction in Europe. Funds are transferred within 2-7 days.',
            },
            4: {
                'title_en': 'Import bank statements',
                'steps_en': [
                    "Download the statement : From your bank, export the statement in CSV, OFX or QIF format.",
                    "Import into MartialComp : From Finances > Import, upload the file. MartialComp detects the format and maps the columns.",
                    "Reconcile : The system automatically matches imported transactions with existing invoices and membership fees.",
                    "Validate : Verify the matches, correct errors and validate. Unmatched transactions are added as pending.",
                ],
                'tip_en': 'Monthly bank imports keep your accounting up to date without manual entry.',
            },
            5: {
                'title_en': 'Manage practitioner membership fees',
                'steps_en': [
                    "Configure rates : From Finances > Membership fees, set annual rates by category: child, teen, adult, family.",
                    "Issue payment requests : At the start of the season, generate payment requests for all members. Each receives an email with a payment link.",
                    "Track payments : View paid, pending and overdue fees. Status appears on each practitioner's record.",
                    "Send reminders : Schedule automatic reminders: 1 week, 2 weeks, 1 month after the due date.",
                ],
                'tip_en': 'Practitioners with overdue membership fees can be blocked from competition registration.',
            },
        },
    },

    # =========================================================================
    # Section 11: Events & Calendar (3 tutorials)
    # =========================================================================
    11: {
        'title_en': 'Events & Calendar',
        'tutorials': {
            1: {
                'title_en': 'Create an event (workshop, gala, AGM)',
                'steps_en': [
                    "Create the event : From Calendar > New event, enter: type (workshop, gala, AGM, open house), title, dates, venue and description.",
                    "Configure registrations : Enable online registration. Set the number of places, fee (free or paid) and registration deadline.",
                    "Publish : Publish the event. It appears in the club calendar and can be shared on social media.",
                ],
                'tip_en': 'Workshops with guest masters are excellent marketing tools. Add their photo and bio to attract more people.',
            },
            2: {
                'title_en': 'Manage recurring events',
                'steps_en': [
                    "Create the recurrence : During creation, check 'Recurring event'. Set the frequency: daily, weekly, monthly.",
                    "Manage exceptions : Cancel or modify an individual occurrence without affecting others (e.g., class cancelled for a public holiday).",
                    "Modify the series : Modify the entire series (e.g., permanent schedule change) or a single occurrence.",
                ],
                'tip_en': 'Weekly classes should be created as recurring events to automatically appear in the calendar.',
            },
            3: {
                'title_en': 'Track registrations and attendance',
                'steps_en': [
                    "View registrants : From the event, view the list of registrants with their status: registered, confirmed, cancelled.",
                    "Record attendance : On the day of the event, record attendance by list or QR code.",
                    "Export : Export the participant list in CSV or PDF for your records.",
                ],
                'tip_en': 'Event attendance rate is a key indicator of your members\' engagement.',
            },
        },
    },

    # =========================================================================
    # Section 12: Family Management (3 tutorials)
    # =========================================================================
    12: {
        'title_en': 'Family Management',
        'tutorials': {
            1: {
                'title_en': 'Create a family group',
                'steps_en': [
                    "Access family groups : From your profile, go to Settings > Family Group > Create.",
                    "Add members : Add each family member: spouse, children. Link their existing MartialComp accounts or create new ones.",
                    "Set the responsible person : The family group manager receives all notifications and manages payments for the entire family.",
                ],
                'tip_en': 'Some clubs offer family rates (discount from the 3rd member). The family group automatically activates these discounts.',
            },
            2: {
                'title_en': 'Register the whole family for a competition',
                'steps_en': [
                    "Group registration : From the competition, click 'Register my family'. Eligible members from your family group are displayed.",
                    "Select and confirm : Select the members to register. Categories are automatically suggested for each one.",
                    "Single payment : Pay all registrations in a single transaction.",
                ],
                'tip_en': 'Group registration saves valuable time when multiple children participate in the same competition.',
            },
            3: {
                'title_en': 'Family payment center',
                'steps_en': [
                    "Overview : The family center displays all membership fees, registrations and invoices for the family on a single screen.",
                    "Group payment : Group multiple pending payments and pay in a single transaction.",
                    "History : View the complete family payment history with downloadable receipts.",
                ],
                'tip_en': 'Enable automatic direct debit so you never forget a membership fee.',
            },
        },
    },

    # =========================================================================
    # Section 13: Task Management (Kanban) (2 tutorials)
    # =========================================================================
    13: {
        'title_en': 'Task Management (Kanban)',
        'tutorials': {
            1: {
                'title_en': 'Use the Kanban board',
                'steps_en': [
                    "Create a board : From Tools > Kanban, create a new board: name, description, and invited members.",
                    "Add columns : Create your workflow columns: To Do, In Progress, On Hold, Done. Customize names and colors.",
                    "Create tasks : Add tasks with: title, description, due date, assignee, priority (high/medium/low) and labels.",
                    "Manage by drag-and-drop : Move tasks between columns by dragging them. Movement history is preserved.",
                ],
                'tip_en': 'Create a dedicated board for each competition to organize. Standard tasks (book the venue, order medals, etc.) can be imported from a template.',
            },
            2: {
                'title_en': 'Manage organizational tasks',
                'steps_en': [
                    "Competition template : Use the 'Competition Organization' template which contains standard tasks: logistics, communication, judges, medals, etc.",
                    "Assign to members : Assign each task to a member of the organizing team. Set deadlines.",
                    "Track progress : The overall progress percentage is displayed at the top of the board. Overdue tasks are highlighted in red.",
                ],
                'tip_en': 'The Kanban board is accessible from the mobile app to update tasks on the go.',
            },
        },
    },

    # =========================================================================
    # Section 14: Online Shop (2 tutorials)
    # =========================================================================
    14: {
        'title_en': 'Online Shop',
        'tutorials': {
            1: {
                'title_en': 'Set up the club shop',
                'steps_en': [
                    "Activate the shop : From Settings > Shop, enable the e-commerce feature. Connect your Stripe account if not already done.",
                    "Add products : Create your products: name, description, photos, price, available sizes/variants, stock.",
                    "Organize by categories : Classify your products: Uniforms (kimono, dobok, gloves), Equipment (protectors, bags), Accessories (belts, patches), Merchandise.",
                    "Publish the shop : Your shop is accessible from your public club page. Share the link or QR code.",
                ],
                'tip_en': 'Offer bundles (kimono + belt + bag) with a discount to increase the average basket.',
            },
            2: {
                'title_en': 'Place an order',
                'steps_en': [
                    "Browse the shop : From your club's page, access the shop. Browse products by category.",
                    "Add to cart : Select the size/variant and add to cart. The cart persists between sessions.",
                    "Order and pay : Validate your cart, choose the delivery method (dojo pickup or postal shipping) and pay online.",
                    "Track the order : Receive notifications at each step: order confirmed, being prepared, ready for pickup / shipped.",
                ],
                'tip_en': 'The \'Dojo Pickup\' mode avoids shipping fees. The coach will hand you your order at the next class.',
            },
        },
    },

    # =========================================================================
    # Section 15: Advanced Features (5 tutorials)
    # =========================================================================
    15: {
        'title_en': 'Advanced Features',
        'tutorials': {
            1: {
                'title_en': 'Set up competition streaming',
                'steps_en': [
                    "Prepare the stream : Create a live event on YouTube, Twitch or Facebook. Copy the stream URL and stream key.",
                    "Configure in MartialComp : From the competition, go to Settings > Streaming. Paste the URL and enable display on the public page.",
                    "Scoring overlay : Enable the MartialComp overlay that displays the live score on the video stream. Customize the position and style.",
                    "Launch and test : Start the stream and verify the overlay works. Viewers see the live score on the stream.",
                ],
                'tip_en': 'Streaming with a MartialComp scoring overlay gives a professional appearance even to small competitions.',
            },
            2: {
                'title_en': 'Use the mobile application',
                'steps_en': [
                    "Download the app : Search for 'MartialComp' on the Play Store (Android) or App Store (iOS). Install and open.",
                    "Log in : Log in with your existing MartialComp account. You can also use Google, Facebook or Apple sign-in.",
                    "Discover the mobile interface : The app offers: profile, results, calendar, push notifications, personal QR code, and competition registration.",
                    "Offline mode : Essential data (profile, grade, license) is available offline. Automatic synchronization when back online.",
                ],
                'tip_en': 'Enable push notifications to be alerted of live results during competitions.',
            },
            3: {
                'title_en': 'Switch roles in the application',
                'steps_en': [
                    "Access the role selector : Tap on your avatar at the top of the screen or swipe from the left to open the side menu.",
                    "Select a role : Your list of roles appears: Coach, Practitioner, Judge, Club Manager. Tap the desired role.",
                    "Adapted interface : The dashboard and menu update immediately to reflect the selected role.",
                ],
                'tip_en': 'You can be a coach in one club and a practitioner in another. Each role is linked to its organization.',
            },
            4: {
                'title_en': 'Advanced data Import/Export',
                'steps_en': [
                    "Supported formats : MartialComp supports import and export in CSV, Excel (XLSX), JSON and PDF. Each module has its own options.",
                    "Import with mapping : The mapping interface allows you to associate any file structure with MartialComp fields.",
                    "Custom export : Select the fields to export, filters, and format. Schedule recurring automatic exports.",
                    "Bulk operations : Bulk operations allow mass modification of: grade, group, membership status, etc.",
                ],
                'tip_en': 'JSON export is ideal for integrations with third-party systems (website, third-party application, CRM).',
            },
            5: {
                'title_en': 'Manage ad-hoc judges (volunteers)',
                'steps_en': [
                    "Create a temporary judge : On competition day, from Judges > Add volunteer, create a temporary profile: name, club and specialty.",
                    "Assign a PIN : A unique PIN is automatically generated. The volunteer uses this PIN to access the scoring interface.",
                    "Assign to categories : Assign the volunteer judge to categories like a regular judge. They can score immediately.",
                    "After the competition : The temporary profile is archived after the competition. Scores are kept in the history.",
                ],
                'tip_en': 'Ad-hoc judges are essential for small competitions where the number of official judges is limited.',
            },
        },
    },
}


class Command(BaseCommand):
    help = 'Translate all 81 tutorials from French to English (hardcoded translations)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be updated without saving to database'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes will be saved'))

        sections_updated = 0
        tutorials_updated = 0
        sections_missing = 0
        tutorials_missing = 0

        for section in TutorialSection.objects.all().order_by('order'):
            sec_data = TRANSLATIONS.get(section.order)
            if not sec_data:
                self.stdout.write(self.style.WARNING(
                    f'  No translation for section {section.order}: {section.title}'
                ))
                sections_missing += 1
                continue

            section.title_en = sec_data['title_en']
            if not dry_run:
                section.save(update_fields=['title_en'])
            sections_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Section {section.order}: {section.title_fr} -> {sec_data["title_en"]}'
            ))

            for tutorial in section.tutorials.all().order_by('number'):
                tut_data = sec_data.get('tutorials', {}).get(tutorial.number)
                if not tut_data:
                    self.stdout.write(self.style.WARNING(
                        f'    No translation for tutorial {section.order}.{tutorial.number}: {tutorial.title}'
                    ))
                    tutorials_missing += 1
                    continue

                tutorial.title_en = tut_data['title_en']
                tutorial.steps_en = json.dumps(tut_data['steps_en'], ensure_ascii=False)
                tutorial.tip_en = tut_data.get('tip_en', '')

                if not dry_run:
                    tutorial.save(update_fields=['title_en', 'steps_en', 'tip_en'])

                tutorials_updated += 1
                self.stdout.write(f'    {section.order}.{tutorial.number}: {tut_data["title_en"]}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Translation complete: {sections_updated} sections, {tutorials_updated} tutorials updated'
        ))
        if sections_missing or tutorials_missing:
            self.stdout.write(self.style.WARNING(
                f'Missing translations: {sections_missing} sections, {tutorials_missing} tutorials'
            ))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes were saved'))
