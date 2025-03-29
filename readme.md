# Google Search Console MCP Server for Claude

This project provides a Model Context Protocol (MCP) server that allows Claude AI (via the Claude Desktop app) to interact with the Google Search Console API. You can use it to query performance data, inspect URLs, check indexing status, and more, directly from your Claude chat.

## Features

Based on the available Google Search Console API endpoints allowed in this project:

*   **Sites:** List accessible sites/properties in your Search Console account.
*   **Search Analytics:** Fetch search performance data (clicks, impressions, CTR, position) with various filters and dimensions.
*   **URL Inspection:** Inspect the status of a specific URL in the Google index, check its indexing status, and request indexing.
*   **Sitemaps:** List submitted sitemaps for a site.
*   **(Helper)** Get an overall site performance summary (derived from Search Analytics data).

*(Note: Index coverage details and crawl errors beyond what's available in the URL Inspection API are generally not exposed via the Google Search Console API.)*

## Prerequisites

*   **Python:** Version 3.11 or higher.
*   **pip:** Python package installer (usually comes with Python).
*   **Virtual Environment Tool:** `venv` (recommended, built into Python 3).
*   **Google Account:** With access to the Google Search Console properties you want to query.
*   **Claude Desktop App:** Installed and running.

## Setup Instructions

1.  **Clone or Download:**
    Get the project files onto your local machine. If using git:
    ```bash
    git clone <your-repository-url>
    cd search-console-mcp
    ```
    *(Replace `<your-repository-url>` if applicable, otherwise just navigate to the downloaded directory)*

2.  **Create and Activate Virtual Environment:**
    It's highly recommended to use a virtual environment to manage dependencies.
    ```bash
    # Create the virtual environment (using the name 'fresh_env' as in previous steps)
    python3 -m venv fresh_env

    # Activate the environment
    # On macOS/Linux:
    source fresh_env/bin/activate
    # On Windows:
    # .\fresh_env\Scripts\activate
    ```
    *(You should see `(fresh_env)` at the beginning of your terminal prompt)*

3.  **Install Dependencies:**
    Install the required Python packages, including the project itself in editable mode.
    ```bash
    pip install -e .
    ```

4.  **Google Cloud Setup & Credentials:**
    *   **Enable API:** Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project or select an existing one. Enable the "Google Search Console API" for your project.
    *   **Create OAuth Credentials:**
        *   Navigate to "APIs & Services" -> "Credentials".
        *   Click "+ CREATE CREDENTIALS" -> "OAuth client ID".
        *   If prompted, configure the "OAuth consent screen" (select "External" user type, provide an app name like "Claude GSC Tool", your email, and save).
        *   For "Application type", select **"Desktop app"**.
        *   Give it a name (e.g., "Claude Desktop GSC Tool").
        *   Click "Create".
    *   **Download `credentials.json`:** After creation, click "DOWNLOAD JSON". Save this file directly into the root of your project directory (`search-console-mcp/`) and ensure it is named exactly `credentials.json`.
    *   **IMPORTANT:** Make sure `credentials.json` is listed in your `.gitignore` file to avoid accidentally committing it.

5.  **Initial Authentication:**
    *   The first time a tool requiring authentication is run (either manually or via Claude), it will trigger the Google OAuth flow.
    *   Your web browser should open, asking you to log in to the Google Account that has access to your Search Console properties.
    *   Grant the requested permissions to the application you configured ("Claude GSC Tool").
    *   After successful authorization, a `token.json` file will be created in your project directory. This stores your access token. **Do not commit `token.json`**.

## Running the Server (Development/Testing)

While the primary use is via Claude Desktop integration, you can test the server directly using `stdio` transport:
