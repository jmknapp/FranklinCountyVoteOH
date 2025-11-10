#!/bin/bash
#
# Deploy the Franklin County Vote Analysis web application
# Deploys to /var/www/html/ionic/fcvote for web access
#

set -e  # Exit on error

# Configuration
DEPLOY_DIR="/var/www/html/ionic/fcvote"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "========================================="
echo "Franklin County Vote Analysis Deployment"
echo "========================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Deploy target: $DEPLOY_DIR"
echo ""

# Check if deploy directory exists, create if not
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "Creating deployment directory..."
    sudo mkdir -p "$DEPLOY_DIR"
    sudo chown $USER:$USER "$DEPLOY_DIR"
fi

# Create directory structure
echo "Setting up directory structure..."
mkdir -p "$DEPLOY_DIR/static"
mkdir -p "$DEPLOY_DIR/templates"
mkdir -p "$DEPLOY_DIR/data"
mkdir -p "$DEPLOY_DIR/docs"

# Copy Flask application
echo "Copying Flask application..."
cp -r "$PROJECT_ROOT/webapp/app.py" "$DEPLOY_DIR/"
cp -r "$PROJECT_ROOT/webapp/templates/"* "$DEPLOY_DIR/templates/"
cp -r "$PROJECT_ROOT/webapp/race_metadata.yaml" "$DEPLOY_DIR/"

# Copy data files (results CSVs, shapefiles, processed data)
echo "Copying data files..."
rsync -av --delete "$PROJECT_ROOT/data/raw/" "$DEPLOY_DIR/data/raw/"
rsync -av --delete "$PROJECT_ROOT/data/processed/" "$DEPLOY_DIR/data/processed/"

# Copy documentation and analysis pages
echo "Copying documentation and analysis pages..."
cp "$PROJECT_ROOT/docs/CD7_RACE_ANALYSIS.html" "$DEPLOY_DIR/docs/"
cp "$PROJECT_ROOT/docs/cd7_election_map.html" "$DEPLOY_DIR/docs/"
cp "$PROJECT_ROOT/README.md" "$DEPLOY_DIR/docs/"

# Copy requirements.txt for reference
cp "$PROJECT_ROOT/requirements.txt" "$DEPLOY_DIR/"

# Create/update symlinks for easy access
echo "Creating convenience symlinks..."
cd "$DEPLOY_DIR"
ln -sf docs/CD7_RACE_ANALYSIS.html cd7_analysis.html
ln -sf docs/cd7_election_map.html cd7_map.html

# Set permissions
echo "Setting permissions..."
sudo chown -R www-data:www-data "$DEPLOY_DIR" || chown -R $USER:$USER "$DEPLOY_DIR"
chmod -R 755 "$DEPLOY_DIR"

# Create a simple index.html for the root
echo "Creating index page..."
cat > "$DEPLOY_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Franklin County Vote Analysis</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            background: white;
            padding: 50px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #1a237e;
            margin-bottom: 20px;
            font-size: 2.5em;
        }
        p {
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
            font-size: 1.1em;
        }
        .links {
            display: grid;
            gap: 15px;
        }
        .link-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            text-decoration: none;
            color: white;
            transition: transform 0.2s, box-shadow 0.2s;
            display: block;
        }
        .link-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .link-card h2 {
            font-size: 1.5em;
            margin-bottom: 10px;
        }
        .link-card p {
            margin: 0;
            color: rgba(255,255,255,0.9);
            font-size: 0.95em;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Franklin County Vote Analysis</h1>
        <p>
            Precinct-level election analysis for Franklin County, Ohio, featuring interactive maps, 
            demographic correlations, and in-depth political analysis.
        </p>
        
        <div class="links">
            <a href="docs/CD7_RACE_ANALYSIS.html" class="link-card">
                <h2>📊 Columbus City Council District 7 Analysis</h2>
                <p>Comprehensive analysis of the 2025 CD7 race with interactive maps and demographic breakdowns</p>
            </a>
            
            <a href="docs/cd7_election_map.html" class="link-card">
                <h2>🗺️ Interactive Election Map</h2>
                <p>Full-page interactive map of CD7 election results by precinct</p>
            </a>
            
            <a href="/fcvote/compare" class="link-card" target="_blank">
                <h2>🔀 Compare Races</h2>
                <p>Interactive web app to compare any two races or ballot issues across years</p>
            </a>
            
            <a href="/fcvote/onemap" class="link-card" target="_blank">
                <h2>🎨 Single Map Viewer</h2>
                <p>View individual race results with customizable color schemes</p>
            </a>
            
            <a href="/fcvote/cluster" class="link-card" target="_blank">
                <h2>📍 Geographic Clustering</h2>
                <p>Analyze spatial patterns and voting clusters using Moran's I</p>
            </a>
            
            <a href="/fcvote/demographics" class="link-card" target="_blank">
                <h2>👥 Demographics Analysis</h2>
                <p>Explore correlations between demographics and voting patterns</p>
            </a>
            
            <a href="/fcvote/cartogram" class="link-card" target="_blank">
                <h2>📐 Turnout Cartogram</h2>
                <p>Visualize precincts sized by voter turnout</p>
            </a>
        </div>
        
        <div class="footer">
            <p>Franklin County Vote Analysis Project | November 2025</p>
            <p><a href="https://github.com/jmknapp/FranklinCountyVoteOH" style="color: #667eea;">View on GitHub</a></p>
        </div>
    </div>
</body>
</html>
EOF

echo ""
echo "========================================="
echo "Deployment complete!"
echo "========================================="
echo ""
echo "📁 Files deployed to: $DEPLOY_DIR"
echo ""
echo "🌐 Access points:"
echo "   Main page:      http://localhost/ionic/fcvote/"
echo "   CD7 Analysis:   http://localhost/ionic/fcvote/docs/CD7_RACE_ANALYSIS.html"
echo "   Election Map:   http://localhost/ionic/fcvote/docs/cd7_election_map.html"
echo ""
echo "🚀 To start the Flask app:"
echo "   cd $DEPLOY_DIR"
echo "   source $PROJECT_ROOT/.venv/bin/activate"
echo "   python app.py"
echo ""
echo "   Or use the systemd service if configured"
echo ""

