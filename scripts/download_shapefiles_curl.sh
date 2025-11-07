#!/bin/bash
# Download Franklin County precinct shapefiles from Board of Elections
# Source: https://vote.franklincountyohio.gov/maps-and-data/gis-shape-files

set -e
BASE_URL="https://vote.franklincountyohio.gov/getmedia"
DATA_DIR="data/raw"

echo "Downloading Franklin County Precinct Shapefiles"
echo "Source: Franklin County Board of Elections"
echo "================================================"

# Function to download a file
download_file() {
    local url=$1
    local output=$2
    curl -sS -L -o "$output" "$url" || {
        echo "  Warning: Failed to download $output"
        return 1
    }
}

# 2024 (use as base year)
echo "Downloading 2024..."
mkdir -p "$DATA_DIR/precincts_2024"
cd "$DATA_DIR/precincts_2024"
download_file "$BASE_URL/f38a9829-9b8a-46d1-9b4b-f60b13edd1f0/Voting-Precincts-G24-cpg" "Voting_Precinct.cpg"
download_file "$BASE_URL/3b52ae22-0869-47f6-a1ad-02f6ae006a7f/Voting-Precincts-G24-dbf" "Voting_Precinct.dbf"
download_file "$BASE_URL/e1e0ffef-67f0-47c5-813c-18af6fe63f4a/Voting-Precincts-G24-prj" "Voting_Precinct.prj"
download_file "$BASE_URL/c2a13ac8-0ebc-4a13-8f41-2d0e44e05e0d/Voting-Precincts-G24-shp" "Voting_Precinct.shp"
download_file "$BASE_URL/ccee4ec0-43f4-4c3f-a77b-0f2b14b2c32c/Voting-Precincts-G24-shx" "Voting_Precinct.shx"
cd ../../..
echo "✓ 2024 complete"

# 2022
echo "Downloading 2022..."
mkdir -p "$DATA_DIR/precincts_2022"
cd "$DATA_DIR/precincts_2022"
download_file "$BASE_URL/282370ad-918d-4de7-9554-ea84be112444/Voting-Precincts-G22-cpg" "Voting_Precinct.cpg"
download_file "$BASE_URL/37ca9e52-ae06-4b7a-9d7e-fa3d9cb4e5dc/Voting-Precincts-G22-dbf" "Voting_Precinct.dbf"
download_file "$BASE_URL/c0ac05ea-da5f-4aa1-963a-fbb8e7cfe1b5/Voting-Precincts-G22-prj" "Voting_Precinct.prj"
download_file "$BASE_URL/1ba3e2e6-bd15-4cc0-93b2-e40c35e29d48/Voting-Precincts-G22-shp" "Voting_Precinct.shp"
download_file "$BASE_URL/fe5f3d8f-c3ae-4c84-9a86-dbba52a22c0c/Voting-Precincts-G22-shx" "Voting_Precinct.shx"
cd ../../..
echo "✓ 2022 complete"

# 2020
echo "Downloading 2020..."
mkdir -p "$DATA_DIR/precincts_2020"
cd "$DATA_DIR/precincts_2020"
download_file "$BASE_URL/76d0ab7d-ccf1-4775-934c-e29e50c73b13/Voting-Precincts-G20-cpg" "Voting_Precinct.cpg"
download_file "$BASE_URL/5f97d28a-6c56-484c-8b1b-e66e9668dbae/Voting-Precincts-G20-dbf" "Voting_Precinct.dbf"
download_file "$BASE_URL/bc9c92cc-8f45-4b04-aac7-cf10ffc2bb55/Voting-Precincts-G20-prj" "Voting_Precinct.prj"
download_file "$BASE_URL/1e8a5eea-4deb-48fc-ba1a-9cabd58e0fc1/Voting-Precincts-G20-shp" "Voting_Precinct.shp"
download_file "$BASE_URL/8c0e7b31-6b36-46a6-b6e0-2f30d8eabc02/Voting-Precincts-G20-shx" "Voting_Precinct.shx"
cd ../../..
echo "✓ 2020 complete"

# 2018
echo "Downloading 2018..."
mkdir -p "$DATA_DIR/precincts_2018"
cd "$DATA_DIR/precincts_2018"
download_file "$BASE_URL/e3f5f9ad-eb6d-43a8-bfff-67c9ae4dd25d/Voting-Precincts-G18-cpg" "Voting_Precinct.cpg"
download_file "$BASE_URL/c3b3a8c3-5ba1-4c18-8a03-9b9a8ea3fa0e/Voting-Precincts-G18-dbf" "Voting_Precinct.dbf"
download_file "$BASE_URL/b8ad5e40-c87e-4e7d-a14e-bf5cfc050eb4/Voting-Precincts-G18-prj" "Voting_Precinct.prj"
download_file "$BASE_URL/db9eed5c-3856-4f1c-abd7-4bff70d23d58/Voting-Precincts-G18-shp" "Voting_Precinct.shp"
download_file "$BASE_URL/d5ef2b8e-dd95-4ddb-a9e4-6e0cb31d1a31/Voting-Precincts-G18-shx" "Voting_Precinct.shx"
cd ../../..
echo "✓ 2018 complete"

# 2016
echo "Downloading 2016..."
mkdir -p "$DATA_DIR/precincts_2016"
cd "$DATA_DIR/precincts_2016"
download_file "$BASE_URL/46d9cb80-8e58-4e6d-ad76-16beb29cd9f6/Voting-Precincts-G16-cpg" "Voting_Precinct.cpg"
download_file "$BASE_URL/8f485fab-a60e-4597-8e43-4f5db23eaa96/Voting-Precincts-G16-dbf" "Voting_Precinct.dbf"
download_file "$BASE_URL/d38ef40e-28a7-4c27-badc-b1b7cd5d5d73/Voting-Precincts-G16-prj" "Voting_Precinct.prj"
download_file "$BASE_URL/72e2fbbb-b7dd-40c8-b8cb-67b8e8f2e14f/Voting-Precincts-G16-shp" "Voting_Precinct.shp"
download_file "$BASE_URL/81b35f42-1df5-4b38-997e-ad3d3bcc4e33/Voting-Precincts-G16-shx" "Voting_Precinct.shx"
cd ../../..
echo "✓ 2016 complete"

# 2014
echo "Downloading 2014..."
mkdir -p "$DATA_DIR/precincts_2014"
cd "$DATA_DIR/precincts_2014"
download_file "$BASE_URL/26ce5e1f-ff75-467e-bdd5-3e8b70024af5/Voting-Precincts-G14-cpg" "Voting_Precinct.cpg"
download_file "$BASE_URL/1e1e4fd0-e8ad-4e01-a3e1-5f7e2a8819eb/Voting-Precincts-G14-dbf" "Voting_Precinct.dbf"
download_file "$BASE_URL/9be6a99a-f506-46e5-b92d-6b7ce89e3dbc/Voting-Precincts-G14-prj" "Voting_Precinct.prj"
download_file "$BASE_URL/ea8e1ba3-f5a0-4fc1-bbd0-ba55a2e84f45/Voting-Precincts-G14-shp" "Voting_Precinct.shp"
download_file "$BASE_URL/cf683ccc-d1f8-4f3d-a5b8-37e8bd19e9e1/Voting-Precincts-G14-shx" "Voting_Precinct.shx"
cd ../../..
echo "✓ 2014 complete"

# 2012
echo "Downloading 2012..."
mkdir -p "$DATA_DIR/precincts_2012"
cd "$DATA_DIR/precincts_2012"
download_file "$BASE_URL/1d6ccbe1-40c0-40f2-9d9f-e3e5e8d43c3e/Precincts_G12-dbf" "Voting_Precinct.dbf"
download_file "$BASE_URL/7d9e99cf-3cc6-42cd-91d5-bc46b01ecfc1/Precincts_G12-prj" "Voting_Precinct.prj"
download_file "$BASE_URL/3b56b01f-6d8f-474e-85de-62d37ed8fea5/Precincts_G12-shp" "Voting_Precinct.shp"
download_file "$BASE_URL/2ee1d1f5-f1f5-40f3-bdfa-86bdc0c1a98e/Precincts_G12-shx" "Voting_Precinct.shx"
cd ../../..
echo "✓ 2012 complete"

# 2010
echo "Downloading 2010..."
mkdir -p "$DATA_DIR/precincts_2010"
cd "$DATA_DIR/precincts_2010"
download_file "$BASE_URL/d37f1b48-c6a0-4aa3-be15-de5f5a3b8e4b/Precincts_G10-dbf" "Voting_Precinct.dbf"
download_file "$BASE_URL/b08f0ae4-af4e-43f7-8ba2-2b3ba5c29f36/Precincts_G10-prj" "Voting_Precinct.prj"
download_file "$BASE_URL/b5f9e3ab-8c16-424a-93f0-c19fe1c8c2f4/Precincts_G10-shp" "Voting_Precinct.shp"
download_file "$BASE_URL/e4e72d74-49e7-453c-a026-baef6a28c99c/Precincts_G10-shx" "Voting_Precinct.shx"
cd ../../..
echo "✓ 2010 complete"

# 2008
echo "Downloading 2008..."
mkdir -p "$DATA_DIR/precincts_2008"
cd "$DATA_DIR/precincts_2008"
download_file "$BASE_URL/fd71c636-ce38-4d51-9572-664a34611dca/Precincts_08-dbf" "Voting_Precinct.dbf"
download_file "$BASE_URL/68580412-31b5-42d5-9bbc-8b62ce212dff/Precincts_08-shp" "Voting_Precinct.shp"
download_file "$BASE_URL/dcd190e0-5271-49e9-bb81-9f1e67d2af09/Precincts_08-shx" "Voting_Precinct.shx"
cd ../../..
echo "✓ 2008 complete (no .prj file available)"

# 2006
echo "Downloading 2006..."
mkdir -p "$DATA_DIR/precincts_2006"
cd "$DATA_DIR/precincts_2006"
download_file "$BASE_URL/82289fcd-f7a0-465d-beac-c4997c9acb81/Precincts_G06-dbf" "Voting_Precinct.dbf"
download_file "$BASE_URL/2eca4be0-e2b2-49c9-9902-88a82fdc764b/Precincts_G06-shp" "Voting_Precinct.shp"
download_file "$BASE_URL/df0621d0-925a-480d-ba6c-2546e2a46d66/Precincts_G06-shx" "Voting_Precinct.shx"
cd ../../..
echo "✓ 2006 complete (no .prj file available)"

echo ""
echo "================================================"
echo "Download complete! Shapefiles for 2006-2024"
echo "Source: Franklin County Board of Elections"
echo "URL: https://vote.franklincountyohio.gov/maps-and-data/gis-shape-files"
echo "================================================"

# Summary
echo ""
echo "Summary:"
for year in 2024 2022 2020 2018 2016 2014 2012 2010 2008 2006; do
    count=$(ls "$DATA_DIR/precincts_$year/" 2>/dev/null | wc -l)
    echo "  $year: $count files"
done

