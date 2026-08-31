echo "Checking if the metabase directory is ready..."
if [ -d 'plugins' ]; then
    echo "The plugins directory already exist, skipping..."
else
    echo "The plugins directory doesn't exist, creating it and fetching the latest duckdb driver for metabase..."
    mkdir plugins
    wget -P ./plugins $(curl -s https://api.github.com/repos/motherduckdb/metabase_duckdb_driver/releases/latest | jq -r '.assets[] | select(.name | endswith(".jar")) | .browser_download_url')
fi

if [ -d 'metabase-data']; then
    echo "The metabase-data directory already exist, skipping..."
else
    echo "The metabase-data directory doesn't exist, creating it..."
    mkdir metabase-data
fi
echo "The metabase directory is ready!"
