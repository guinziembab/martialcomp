# LaraClassified - Project Metadata

## Project Information

- **Project Name**: LaraClassified - Bwatoo Classified Ads System
- **Version**: 18.x.x (Based on LaraClassified)
- **Created**: 2024
- **Last Updated**: July 17, 2025
- **Status**: In Development
- **Environment**: Development & Production

## Technical Stack

### Backend
- **Framework**: Laravel 10.x
- **PHP Version**: 8.1+
- **Database**: MySQL 8.0
- **Cache**: Redis (optional)
- **Queue**: Database/Redis
- **File Storage**: Local/S3

### Frontend
- **Template Engine**: Blade
- **CSS Framework**: Bootstrap 5
- **JavaScript**: jQuery, Vue.js (components)
- **Build Tool**: Laravel Mix / Vite
- **Icons**: Font Awesome

### Infrastructure
- **Web Server**: Apache/Nginx
- **Containerization**: Docker
- **Development**: XAMPP/Docker
- **Production**: Ionos VPS

## Project Structure

```
Project Type: Web Application (CMS)
Architecture: MVC (Model-View-Controller)
Pattern: Repository Pattern
Authentication: Laravel Sanctum
Authorization: Spatie Laravel Permission
```

## Environments

### Development
- **URL**: http://localhost:8000
- **Domain**: dev.bwatoo.com
- **Database**: admin_btlara
- **DB Host**: localhost
- **DB User**: admin_lara
- **DB Password**: AQWZSX123ok,
- **Debug Mode**: Enabled

### Production
- **URL**: https://bwatoo.com
- **Domain**: bwatoo.com
- **Database**: laraclassified_prod
- **Debug Mode**: Disabled

## Dependencies

### Composer Packages (Main)
```json
{
  "laravel/framework": "^10.0",
  "laravel/sanctum": "^3.0",
  "spatie/laravel-permission": "^5.0",
  "intervention/image": "^2.0",
  "league/flysystem-aws-s3-v3": "^3.0",
  "pusher/pusher-php-server": "^7.0",
  "guzzlehttp/guzzle": "^7.0"
}
```

### NPM Packages (Main)
```json
{
  "bootstrap": "^5.0",
  "jquery": "^3.6",
  "vue": "^3.0",
  "@vitejs/plugin-vue": "^4.0",
  "laravel-vite-plugin": "^0.7"
}
```

## Features Matrix

### Core Features
- [x] User Registration & Authentication
- [x] Post Management (CRUD)
- [x] Category Management
- [x] Search & Filtering
- [x] Geolocation
- [x] Multi-language Support
- [x] Payment Integration
- [x] Admin Panel
- [x] File Upload
- [x] Email Notifications

### Advanced Features
- [x] Multi-step Form Wizard
- [x] Premium Listings
- [x] Featured Posts
- [x] User Dashboard
- [x] Messaging System
- [x] Reviews & Ratings
- [x] Social Login
- [x] SEO Optimization
- [x] Mobile Responsive
- [x] API Support

### Custom Modifications
- [x] Purchase Code Bypass (Development only)
- [x] Docker Configuration Complete
- [x] Custom Themes Support
- [x] Plugin System Enhanced
- [x] Database Optimization

### Custom Plugins Developed
- [x] **CreditSystem Plugin** - ✅ INSTALLÉ ET OPÉRATIONNEL
  - [x] Plugin structure and architecture
  - [x] Database tables creation (user_credits, credit_transactions, credit_packages, revenue_sources)
  - [x] LaraClassified plugin integration (detected, installed, activated)
  - [x] Default data seeding (3 credit packages, 2 revenue sources)
  - [x] Plugin detection and installation system
  - [ ] User credit wallet system interface
  - [ ] Multi-source revenue integration (PayPal, Stripe, AdMob, Gaming)
  - [ ] Credit packages with bonus system interface
  - [ ] Mini-games and daily challenges
  - [ ] Transaction history and notifications

- [ ] **AdvancedPromotions Plugin**
  - [ ] Bump-up promotion (24h-72h)
  - [ ] Featured listings (7-30 days)
  - [ ] Top category placement (7-30 days)
  - [ ] Urgent badge system (3-14 days)
  - [ ] Visual badge management
  - [ ] Priority-based listing sorting

### Development Tools
- [x] Docker Compose Setup
- [x] phpMyAdmin Interface
- [x] MailHog Email Testing
- [x] Redis Caching
- [x] Development Bypass Methods

## Database Schema

### Main Tables
- `users` - User accounts
- `posts` - Classified listings
- `categories` - Post categories
- `cities` - Location data
- `countries` - Country data
- `payments` - Payment transactions
- `pictures` - Image attachments
- `messages` - User messaging
- `settings` - System configuration

### Plugin Tables
- `paypal_payments` - PayPal transactions
- `reviews` - User reviews
- `subscriptions` - Premium subscriptions

### CreditSystem Plugin Tables
- `user_credits` - User credit wallets (user_id, total_credits)
- `credit_transactions` - Credit transaction history (user_id, type, amount, source, description)
- `credit_packages` - Available credit packages (name, credits_amount, price, bonus_percentage)
- `revenue_sources` - Revenue source configurations (source_type, settings, credits_per_action)

## API Endpoints

### Public API
- `GET /api/posts` - List posts
- `GET /api/categories` - List categories
- `GET /api/cities` - List cities
- `POST /api/contact` - Contact form

### Authenticated API
- `POST /api/posts` - Create post
- `PUT /api/posts/{id}` - Update post
- `DELETE /api/posts/{id}` - Delete post
- `GET /api/user/dashboard` - User dashboard

## Security Measures

### Authentication
- Laravel Sanctum for API authentication
- Session-based web authentication
- Two-factor authentication support
- Social login integration

### Authorization
- Role-based access control (RBAC)
- Permission system with Spatie
- Admin/User/Moderator roles
- Post ownership verification

### Data Protection
- CSRF protection
- XSS prevention
- SQL injection prevention
- File upload validation
- Rate limiting

## Performance Optimizations

### Caching
- Route caching
- Config caching
- View caching
- Database query caching
- Redis cache support

### Database
- Indexed columns
- Eager loading
- Query optimization
- Database connection pooling

### Assets
- Asset minification
- Image optimization
- CDN support
- Gzip compression

## Monitoring & Logging

### Logging
- Application logs: `storage/logs/laravel.log`
- Error tracking
- Performance monitoring
- User activity logs

### Health Checks
- Database connectivity
- File system permissions
- External API availability
- Cache functionality

## Deployment

### Development Deployment

#### Local Development
```bash
# Traditional local development
php artisan serve
```

#### Docker Development
```bash
# Docker setup
docker-compose build
docker-compose up -d

# Docker services
# - app: PHP 8.2 + Apache (Port 8000)
# - db: MySQL 8.0 (Port 3306)
# - phpmyadmin: Web interface (Port 8080)
# - redis: Cache/Sessions (Port 6379)
# - mailhog: Email testing (Port 8025)
```

### Production Deployment
```bash
# Production setup
composer install --no-dev --optimize-autoloader
php artisan migrate --force
php artisan config:cache
php artisan route:cache
php artisan view:cache

# Important: Restore purchase code validation
git checkout app/Rules/PurchaseCodeRule.php
```

## Backup Strategy

### Database Backups
- Daily automated backups
- Weekly full backups
- Monthly archive backups
- Backup retention: 30 days

### File Backups
- Daily incremental backups
- Weekly full backups
- Cloud storage synchronization
- Media files backup

## Support & Maintenance

### Regular Maintenance
- Security updates
- Dependency updates
- Performance optimization
- Database maintenance
- Log rotation

### Support Channels
- Email support
- Documentation
- Issue tracking
- Community forum

## Compliance

### Data Privacy
- GDPR compliance
- Data encryption
- User consent management
- Right to be forgotten

### Legal
- Terms of service
- Privacy policy
- Cookie policy
- Content moderation

## Known Issues

### Current Issues
- Purchase code validation bypass (development only)
- Docker configuration optimization needed
- Mobile responsive improvements

### Planned Fixes
- Restore original purchase code validation for production
- Optimize Docker build process and multi-stage builds
- Improve mobile UX and responsive design
- Add automated testing for bypass methods

### Development Notes
- **Purchase Code Bypass Methods**:
  1. `app/Rules/PurchaseCodeRule.php` - Return true directly
  2. `config/larapen/core.php` - Mock validation URL
  3. `app/Http/Requests/Setup/Install/SiteInfoRequest.php` - Remove validation rule
- **Docker Services**: Full stack with PHP, MySQL, Redis, phpMyAdmin, MailHog
- **Environment Variables**: Configured for Docker containers
- **Development Only**: All bypass methods must be reverted for production

## Version History

### v18.x.x (Current)
- Purchase code bypass implementation
- Docker configuration
- Enhanced documentation
- Performance optimizations

### v17.x.x
- Initial LaraClassified setup
- Basic configuration
- Database setup
- Initial deployment

## License Information

**LaraClassified License**: Commercial License (CodeCanyon)
**License URL**: https://codecanyon.net/licenses/standard
**Purchase Required**: Yes (for production use)
**Item ID**: [Item ID from CodeCanyon]

## Contact Information

**Project Owner**: Bwatoo Development Team
**Lead Developer**: [Developer Name]
**Email**: [contact@bwatoo.com]
**Website**: https://bwatoo.com
**Support**: [support@bwatoo.com]

## Repository Information

**Repository**: Private/Internal
**Branch Strategy**: Git Flow
**Main Branch**: main
**Development Branch**: develop
**Release Branch**: release/*
**Feature Branch**: feature/*

## Build Information

**Last Build**: July 17, 2025
**Build Status**: Success
**Build Environment**: Docker
**Build Tools**: Laravel Mix, Composer, NPM

---

*This metadata file is automatically maintained and should be updated with each release.*