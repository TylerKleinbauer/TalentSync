# TalentSync

TalentSync is an intelligent job matching platform that uses advanced AI to create personalized professional profiles and match candidates with the most suitable job opportunities.

## Features

### Profile Management
- **Profile Creation**: AI-powered system that creates detailed professional profiles from CVs and cover letters
- **Profile Editing**: Interactive feedback loop allowing users to refine and customize their profiles
- **Smart Profile Storage**: Secure database storage of user profiles with easy access and updates

### Job Matching
- **Intelligent Matching**: Uses OpenAI embeddings for semantic similarity search to find relevant job opportunities
- **Detailed Evaluation**: In-depth analysis of job fit using GPT-4, considering:
  - Core expertise alignment
  - Career trajectory
  - Technical skills match
  - Cultural fit
  - Growth potential
- **Comprehensive Scoring**: Each job match includes:
  - Numerical fit score
  - Detailed evaluation explanation
  - Job details and company information

## Technical Stack

### Backend
- Django framework for robust API and database management
- LangGraph for orchestrating AI workflows
- OpenAI's GPT-4 for intelligent profile creation and job matching
- ChromaDB for efficient similarity search
- Custom state management for complex AI interactions

### Data Models
- Custom User model for authentication and profile linking
- Professional Profile model storing detailed user information
- Job model for storing and managing job listings
- Evaluation models for storing match results

## Future Enhancements

- React frontend for user interaction
- Enhanced job search parameters
- User feedback integration for improved matching
- Additional profile customization options
- Integration with more job platforms
- Real-time job alerts and notifications

## License

This project is licensed under the MIT License - see the LICENSE file for details.