# Production Deployment Guide

## 1. PostgreSQL Database Setup

### Option A: Vercel Postgres (Recommended)
1. Go to your Vercel dashboard
2. Select your project
3. Go to Storage tab
4. Create a new Postgres database
5. Copy the `POSTGRES_URL` connection string

### Option B: External PostgreSQL (Neon, Supabase, etc.)
1. Create account at Neon.tech or Supabase
2. Create new database
3. Get connection string in format: `postgresql://user:password@host:port/database`

## 2. Environment Variables in Vercel

Go to your Vercel project → Settings → Environment Variables and add:

```
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this
ALLOWED_HOSTS=.vercel.app,.caribou-area-management.com
DATABASE_URL=postgresql://user:password@host:port/database
USE_S3=True
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

## 3. AWS S3 Setup for Media Files

### Create S3 Bucket
1. Login to AWS Console
2. Go to S3 service
3. Create new bucket (e.g., `caribou-media-files`)
4. Set region (e.g., `us-east-1`)
5. Uncheck "Block all public access"
6. Enable versioning (optional)

### Create IAM User
1. Go to IAM service
2. Create new user (e.g., `caribou-s3-user`)
3. Attach policy: `AmazonS3FullAccess`
4. Generate Access Key ID and Secret Access Key

### Bucket Policy (Optional - for public read access)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

## 4. Static Files Configuration

The build script automatically handles static files collection. Files are served from:
- Development: Local `/static/` directory
- Production: AWS S3 bucket (if configured) or Vercel static serving

## 5. Database Migration

After deployment, run migrations:
1. Go to Vercel dashboard
2. Functions tab → View Function Logs
3. Or use Vercel CLI: `vercel env pull` then `python manage.py migrate`

## 6. Create Superuser

Connect to your production database and create admin user:
```bash
python manage.py createsuperuser
```

## 7. Security Checklist

✅ **Environment Variables Set**
- DEBUG=False
- Strong SECRET_KEY
- Proper ALLOWED_HOSTS

✅ **Database Configured**
- PostgreSQL connection string
- SSL enabled

✅ **Media Files**
- AWS S3 bucket created
- IAM user with proper permissions
- Bucket policy configured

✅ **SSL/HTTPS**
- Vercel automatically provides SSL
- Security headers enabled in production

## 8. Monitoring & Maintenance

### Health Checks
- Monitor Vercel function logs
- Check database connection
- Verify S3 file uploads

### Backup Strategy
- Database: Automated backups (Vercel Postgres)
- Media Files: S3 versioning enabled
- Code: Git repository

### Performance Optimization
- Enable S3 CloudFront (CDN)
- Database connection pooling
- Static file compression

## 9. Troubleshooting

### Common Issues
1. **Static files not loading**: Check S3 configuration and CORS
2. **Database connection errors**: Verify DATABASE_URL format
3. **File upload failures**: Check AWS credentials and bucket permissions
4. **CSRF errors**: Ensure ALLOWED_HOSTS includes your domain

### Debug Commands
```bash
# Check environment variables
vercel env ls

# View function logs
vercel logs

# Test database connection
python manage.py dbshell
```