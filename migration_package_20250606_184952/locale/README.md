# Internationalization and Localization Guide

This directory contains translation files for the MartialComp application. These files allow the application to be displayed in multiple languages.

## Project Configuration

The following languages are currently supported:
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

## Translation Files

- Each supported language has its own directory (`fr`, `en`, `es`, etc.) with a `LC_MESSAGES` subdirectory
- Inside `LC_MESSAGES`, there is a `django.po` file containing the message strings for that language
- After compilation, there will also be a `django.mo` file, which is the binary version used by Django

## Working with Translations

### Extracting Messages

To extract all translatable strings from the source code and templates, run:

```bash
python manage.py makemessages -l fr  # For French
python manage.py makemessages -l en  # For English
python manage.py makemessages -l es  # For Spanish
# ... etc. for other languages
```

To extract messages for all languages at once:

```bash
python manage.py makemessages -a
```

### Compiling Messages

After editing the `.po` files, you need to compile them to `.mo` files for Django to use them:

```bash
python manage.py compilemessages
```

### Adding a New Language

To add support for a new language:

1. Add the language code and name to the `LANGUAGES` list in `settings.py`
2. Generate the message file: `python manage.py makemessages -l <language_code>`
3. Edit the generated `.po` file with translations
4. Compile the messages: `python manage.py compilemessages`

## Marking Strings for Translation in Templates

In Django templates, strings can be marked for translation using:

```html
{% load i18n %}

<!-- Simple translation -->
{% translate "Text to translate" %}

<!-- Translation with variables -->
{% blocktranslate %}
    Hello, {{ username }}!
{% endblocktranslate %}
```

## Marking Strings for Translation in Python Code

In Python code, strings can be marked for translation using:

```python
from django.utils.translation import gettext as _

# Simple translation
message = _("Text to translate")

# Translation with variables
message = _("Hello, {username}!").format(username=user.username)
```

## Language Selection

Users can change the language using the language selector in the site header. The selection is stored in the user's session.

## References

- [Django Translation Documentation](https://docs.djangoproject.com/en/5.1/topics/i18n/translation/)
- [GNU gettext utilities](https://www.gnu.org/software/gettext/)