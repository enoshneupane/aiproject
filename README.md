# AG Hotels Assistant

A Streamlit app that provides information about AG Hotels using AI.

## Features

- Chat interface to ask questions about AG Hotels properties
- Answers based on hotel information from data files
- Debug information and logs for troubleshooting

## Local Setup

1. Clone the repository
   ```
   git clone https://github.com/enoshneupane/aiproject.git
   cd aiproject
   ```

2. Install dependencies
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your OpenAI API key
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

4. Run the Streamlit app
   ```
   streamlit run streamlit_app.py
   ```

## Deploying to Streamlit Cloud

1. Push your code to GitHub
   ```
   git add .
   git commit -m "Ready for deployment"
   git push
   ```

2. Go to [Streamlit Cloud](https://streamlit.io/cloud) and sign in

3. Create a new app and connect to your GitHub repository:
   - Repository: `enoshneupane/aiproject`
   - Branch: `main`
   - Main file path: `streamlit_app.py`

4. Add your OpenAI API key in the Streamlit Cloud secrets:
   - Go to your app settings
   - Edit Secrets
   - Add the following:
     ```
     OPENAI_API_KEY="your_api_key_here"
     ```

5. Deploy the app

## Data Structure

The app uses text files in the `data/` directory:
- `location.txt`: Information about hotel locations, rooms, and amenities
- `weddings.txt`: Information about wedding venues and packages
- `hotel_data.txt`: General information about AG Hotels

## Troubleshooting

If you encounter issues with the app:
1. Check that your OpenAI API key is correctly set
2. Verify that all data files exist in the `data/` directory
3. Check the logs in the Debug Information section 