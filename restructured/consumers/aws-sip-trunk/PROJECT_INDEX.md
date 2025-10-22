# AWS SIP Trunk Project Index

Complete file reference for the AWS SIP trunk deployment project.

## 📋 Quick Navigation

- **Getting Started**: [QUICKSTART.md](QUICKSTART.md)
- **Full Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Project Overview**: [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)

## 📁 File Structure

```
aws-sip-trunk/
├── Documentation Files
│   ├── README.md                     # Project overview and introduction
│   ├── QUICKSTART.md                 # 5-minute setup guide
│   ├── DEPLOYMENT_SUMMARY.md         # Architecture and design decisions
│   ├── PROJECT_INDEX.md              # This file
│   └── docs/
│       ├── DEPLOYMENT.md             # Detailed deployment instructions
│       └── TROUBLESHOOTING.md        # Issue resolution guide
│
├── Infrastructure as Code
│   └── terraform/
│       ├── main.tf                   # Core Terraform configuration
│       ├── variables.tf              # Input variable definitions
│       ├── outputs.tf                # Output value definitions
│       ├── networking.tf             # VPC, subnets, security groups
│       ├── ec2.tf                    # EC2 instances, IAM roles
│       ├── storage.tf                # S3 buckets, Parameter Store
│       ├── monitoring.tf             # CloudWatch alarms, dashboard
│       └── terraform.tfvars.example  # Example configuration
│
├── Deployment Scripts
│   └── scripts/
│       ├── deploy-asterisk-aws.sh    # Manual AWS CLI deployment
│       └── user-data.sh              # EC2 bootstrap script
│
├── Configuration Templates
│   └── config/
│       ├── pjsip.conf.j2             # PJSIP Jinja2 template
│       ├── extensions.conf.j2        # Dialplan Jinja2 template
│       └── rtp.conf                  # RTP configuration
│
├── Testing
│   └── tests/
│       └── test_sip_connectivity.py  # Integration tests
│
└── Project Configuration
    ├── pyproject.toml                # Python project metadata
    └── .gitignore                    # Git exclusions
```

## 📄 File Descriptions

### Documentation

#### [README.md](README.md)
- **Purpose**: Main project documentation and entry point
- **Audience**: All users
- **Contains**: 
  - Project overview and features
  - AWS services used
  - Design patterns
  - Known issues summary
  - Deployment script overview
  - Environment variables reference

#### [QUICKSTART.md](QUICKSTART.md)
- **Purpose**: Fast-track deployment guide
- **Audience**: Users who want to deploy quickly
- **Contains**:
  - Prerequisites checklist
  - 5-minute Terraform setup
  - ElevenLabs configuration steps
  - Quick troubleshooting
  - Production checklist
  - Cost estimates

#### [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
- **Purpose**: Comprehensive project summary
- **Audience**: Technical decision makers, architects
- **Contains**:
  - Architecture diagrams
  - AWS resources detailed list
  - Configuration file explanations
  - Testing procedures
  - Security best practices
  - Maintenance procedures

#### [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Purpose**: Step-by-step deployment instructions
- **Audience**: DevOps engineers, system administrators
- **Contains**:
  - Detailed prerequisites
  - Two deployment methods (Terraform + Manual)
  - Post-deployment configuration
  - Monitoring setup
  - Backup/restore procedures
  - Scaling and HA configuration

#### [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Purpose**: Comprehensive issue resolution guide
- **Audience**: Operations team, support engineers
- **Contains**:
  - Quick diagnostic commands
  - 9 common issues with solutions
  - Emergency procedures
  - Performance tuning
  - Diagnostic report script

### Infrastructure as Code (Terraform)

#### [terraform/main.tf](terraform/main.tf)
- **Purpose**: Core Terraform configuration
- **Resources**: Provider, data sources, local variables
- **Key Components**:
  - AWS provider configuration
  - Default tags
  - Amazon Linux 2 AMI lookup
  - Version requirements

#### [terraform/variables.tf](terraform/variables.tf)
- **Purpose**: Input variable definitions with validation
- **Variables** (27 total):
  - AWS configuration (region, instance type)
  - Network settings (VPC CIDR, subnets)
  - ElevenLabs credentials
  - Feature flags (HA, TLS, recordings)
  - Monitoring configuration
  - DNS settings

#### [terraform/outputs.tf](terraform/outputs.tf)
- **Purpose**: Export deployment information
- **Outputs** (20 total):
  - Instance IDs and IPs
  - SIP endpoint URI
  - S3 bucket names
  - CloudWatch resources
  - SSH commands
  - Deployment summary

#### [terraform/networking.tf](terraform/networking.tf)
- **Purpose**: Network infrastructure
- **Resources**:
  - VPC with DNS enabled
  - Internet Gateway
  - Public subnets (2x for HA)
  - Route tables
  - Elastic IPs (1-2)
  - Security Groups with rules
  - Route 53 DNS records (optional)

#### [terraform/ec2.tf](terraform/ec2.tf)
- **Purpose**: Compute resources
- **Resources**:
  - IAM role and policies
  - Instance profile
  - EC2 instances (primary + optional standby)
  - EBS volumes
  - CloudWatch log groups
  - User data script integration

#### [terraform/storage.tf](terraform/storage.tf)
- **Purpose**: Storage and secrets management
- **Resources**:
  - S3 bucket for recordings (encrypted, versioned)
  - S3 bucket for backups (optional)
  - Lifecycle policies
  - Parameter Store parameters (3x)
  - Public access blocks

#### [terraform/monitoring.tf](terraform/monitoring.tf)
- **Purpose**: Observability infrastructure
- **Resources**:
  - SNS topic for alarms
  - CloudWatch alarms (6x):
    - Instance status check
    - CPU utilization
    - Memory utilization
    - Disk space
    - SIP registration failures
    - Call failure rate
  - Log metric filters
  - CloudWatch dashboard

#### [terraform/terraform.tfvars.example](terraform/terraform.tfvars.example)
- **Purpose**: Example configuration file
- **Usage**: Copy to `terraform.tfvars` and customize
- **Contains**: All configurable variables with examples

### Deployment Scripts

#### [scripts/deploy-asterisk-aws.sh](scripts/deploy-asterisk-aws.sh)
- **Purpose**: Manual deployment using AWS CLI
- **When to Use**: Alternative to Terraform, one-time deployments
- **Steps**:
  1. Create VPC and networking (10 steps)
  2. Configure Security Groups
  3. Allocate Elastic IP
  4. Store credentials in Parameter Store
  5. Create IAM roles
  6. Launch EC2 instance
  7. Associate Elastic IP
- **Requirements**: AWS CLI, environment variables set
- **Execution Time**: ~20-25 minutes

#### [scripts/user-data.sh](scripts/user-data.sh)
- **Purpose**: EC2 instance bootstrap script
- **Execution**: Runs on first boot via EC2 user data
- **Actions**:
  1. Update system packages
  2. Install build dependencies
  3. Download and compile Asterisk 21
  4. Configure PJSIP, RTP, dialplan
  5. Set up systemd service
  6. Configure Fail2Ban
  7. Install CloudWatch agent
  8. Create health check script
- **Execution Time**: ~15-20 minutes
- **Logs**: `/var/log/asterisk-setup.log`

### Configuration Templates

#### [config/pjsip.conf.j2](config/pjsip.conf.j2)
- **Purpose**: PJSIP configuration template
- **Format**: Jinja2 template
- **Sections**:
  - Global settings
  - Transport configuration (TCP/TLS)
  - Endpoint definition
  - AOR (Address of Record)
  - Authentication
  - Identify rules
  - ACL (optional)
  - Custom endpoints support
- **Template Variables**: 20+ customizable parameters

#### [config/extensions.conf.j2](config/extensions.conf.j2)
- **Purpose**: Asterisk dialplan template
- **Format**: Jinja2 template
- **Contexts**:
  - `from-elevenlabs`: Inbound calls
  - `outbound-to-elevenlabs`: Outbound calls
  - `default`: Unauthorized calls
  - `health-check`: Monitoring endpoint
  - Custom contexts support
- **Features**:
  - Call recording with S3 upload
  - IVR menu system
  - DTMF handling
  - Hangup handlers
  - CDR tracking

### Testing

#### [tests/test_sip_connectivity.py](tests/test_sip_connectivity.py)
- **Purpose**: Integration test suite
- **Framework**: pytest
- **Test Classes**:
  - `TestSIPConnectivity`: Infrastructure and connectivity (9 tests)
  - `TestSIPRegistration`: SIP endpoint configuration
  - `TestCallFlow`: Call establishment and audio
  - `TestMonitoring`: CloudWatch alarms and dashboards
- **Requirements**: boto3, AWS credentials, deployed infrastructure
- **Execution**: `pytest tests/test_sip_connectivity.py`

### Project Configuration

#### [pyproject.toml](pyproject.toml)
- **Purpose**: Python project metadata and dependencies
- **Build System**: setuptools >= 68
- **Dependencies**:
  - boto3, botocore (AWS SDK)
  - pyyaml, jinja2 (configuration)
  - python-dotenv (environment)
- **Dev Dependencies**:
  - pytest, pytest-cov (testing)
  - mypy, ruff, black (linting)
- **Scripts**: `aws-sip-deploy` CLI command

#### [.gitignore](.gitignore)
- **Purpose**: Git exclusions for sensitive and generated files
- **Excludes**:
  - Terraform state files
  - AWS credentials
  - SSH keys
  - Logs and temporary files
  - IDE configurations

## 🔗 File Relationships

### Deployment Flow
```
1. terraform.tfvars
   ↓
2. main.tf + variables.tf
   ↓
3. networking.tf → ec2.tf → storage.tf → monitoring.tf
   ↓
4. user-data.sh (runs on EC2)
   ↓
5. pjsip.conf.j2 + extensions.conf.j2 (generated)
   ↓
6. Asterisk running with SIP trunk
```

### Documentation Flow
```
README.md (overview)
   ↓
QUICKSTART.md (fast start)
   ↓
docs/DEPLOYMENT.md (detailed setup)
   ↓
docs/TROUBLESHOOTING.md (issue resolution)
```

## 🎯 Use Cases by Role

### DevOps Engineer
**Primary Files:**
1. `terraform/` - Infrastructure provisioning
2. `scripts/deploy-asterisk-aws.sh` - Manual deployment
3. `docs/DEPLOYMENT.md` - Deployment procedures
4. `docs/TROUBLESHOOTING.md` - Issue resolution

### System Administrator
**Primary Files:**
1. `QUICKSTART.md` - Fast deployment
2. `config/pjsip.conf.j2` - SIP configuration
3. `config/extensions.conf.j2` - Dialplan customization
4. `docs/TROUBLESHOOTING.md` - Operations guide

### Developer
**Primary Files:**
1. `pyproject.toml` - Project setup
2. `tests/test_sip_connectivity.py` - Integration tests
3. `config/*.j2` - Configuration templates
4. `DEPLOYMENT_SUMMARY.md` - Architecture understanding

### Technical Architect
**Primary Files:**
1. `DEPLOYMENT_SUMMARY.md` - Architecture overview
2. `README.md` - Design patterns
3. `terraform/*.tf` - Infrastructure design
4. `docs/DEPLOYMENT.md` - Deployment options

## 📊 File Statistics

- **Total Files**: 18 main files
- **Terraform Files**: 7 (main + 6 modules)
- **Documentation Files**: 6
- **Scripts**: 2
- **Configuration Templates**: 2
- **Tests**: 1

## 🔐 Security-Sensitive Files

**Never Commit to Git:**
- `terraform.tfvars` (contains credentials)
- `*.pem` (SSH keys)
- `*.key` (TLS private keys)
- `.env` (environment variables)

**Encrypted Storage:**
- ElevenLabs credentials → Parameter Store (AWS)
- SIP passwords → Parameter Store (AWS)
- TLS certificates → S3 with encryption

## 🔄 Update Frequency

| File | Update Frequency | Reason |
|------|-----------------|--------|
| `terraform/*.tf` | Quarterly | AWS provider updates |
| `scripts/user-data.sh` | As needed | Asterisk version updates |
| `config/*.j2` | As needed | Configuration changes |
| `docs/*.md` | Monthly | Documentation improvements |
| `tests/*.py` | As needed | New test scenarios |

## 📞 Support

For questions about specific files:
1. Check file header comments
2. Review related documentation
3. Consult [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
4. Create issue in project repository

---

**Last Updated**: 2025-10-01  
**Project Version**: 1.0.0  
**Maintained By**: MCP Project Orchestrator
