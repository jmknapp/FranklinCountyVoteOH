#!/bin/bash
# Download Franklin County precinct shapefiles from Board of Elections website
# Source: https://vote.franklincountyohio.gov/maps-and-data/gis-shape-files

set -e

BASE_URL="https://vote.franklincountyohio.gov"
DATA_DIR="data/raw"

echo "=========================================="
echo "Franklin County Shapefile Downloader"
echo "=========================================="
echo ""

mkdir -p "$DATA_DIR"

# Function to download a file
download_file() {
    local uuid=$1
    local filename=$2
    local output_path=$3
    
    local url="${BASE_URL}/getmedia/${uuid}/${filename}"
    
    echo "  Downloading: $filename"
    wget -q --no-check-certificate -O "$output_path" "$url" || curl -sL -o "$output_path" "$url"
}

# 2025 - Voting Precinct files
echo "Downloading 2025 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2025"
download_file "8d0f697c-9599-42a8-ac7c-b874c83bdc70" "Voting_Precinct_cpg" "$DATA_DIR/precincts_2025/Voting_Precinct.cpg"
download_file "65bd6003-91e0-497a-b1ba-f07c0ba5195e" "Voting_Precinct_dbf" "$DATA_DIR/precincts_2025/Voting_Precinct.dbf"
download_file "33541603-81d5-4c69-8608-331117b8d62a" "Voting_Precinct_prj" "$DATA_DIR/precincts_2025/Voting_Precinct.prj"
download_file "0c4c0878-2fa8-42ff-a2f2-898c9f8060e0" "Voting_Precinct_sbn" "$DATA_DIR/precincts_2025/Voting_Precinct.sbn"
download_file "9514476b-8358-40e4-836c-c0ce6f76cdec" "Voting_Precinct_sbx" "$DATA_DIR/precincts_2025/Voting_Precinct.sbx"
download_file "59989478-b4b8-4562-bef0-ad34d50829bd" "Voting_Precinct_shp" "$DATA_DIR/precincts_2025/Voting_Precinct.shp"
download_file "59e6d59c-d860-4427-b796-ad1566cff87c" "Voting_Precinct_shx" "$DATA_DIR/precincts_2025/Voting_Precinct.shx"

# 2023 - Voting Precinct files
echo "Downloading 2023 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2023"
download_file "bd7060e5-0c5b-4997-bac6-8d0cee2028a5" "Voting_Precinct_cpg" "$DATA_DIR/precincts_2023/Voting_Precinct.cpg"
download_file "f2d859aa-f107-4ac7-8f78-916c16355365" "Voting_Precinct_dbf" "$DATA_DIR/precincts_2023/Voting_Precinct.dbf"
download_file "d728dea4-98b4-475a-9238-9a343239d64f" "Voting_Precinct_prj" "$DATA_DIR/precincts_2023/Voting_Precinct.prj"
download_file "9b7b4092-cf4e-46eb-8950-c2e1d1192789" "Voting_Precinct_sbn" "$DATA_DIR/precincts_2023/Voting_Precinct.sbn"
download_file "ba0d5f81-0527-4734-b5a0-5d68f7f6f1aa" "Voting_Precinct_sbx" "$DATA_DIR/precincts_2023/Voting_Precinct.sbx"
download_file "11000da7-3309-4a6a-8b21-23c4d8cccbea" "Voting_Precinct_shp" "$DATA_DIR/precincts_2023/Voting_Precinct.shp"
download_file "2e0c38af-aa90-417e-aa21-8c2af73d531e" "Voting_Precinct_shx" "$DATA_DIR/precincts_2023/Voting_Precinct.shx"

# 2022 - Voting Precincts G22
echo "Downloading 2022 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2022"
download_file "282370ad-918d-4de7-9554-ea84be112444" "Voting-Precincts-G22-cpg" "$DATA_DIR/precincts_2022/Voting-Precincts-G22.cpg"
download_file "29c65037-35be-4bdb-82dc-f065d49bad7d" "Voting-Precincts-G22-dbf" "$DATA_DIR/precincts_2022/Voting-Precincts-G22.dbf"
download_file "18f80bff-e4da-408a-91f0-5dd27ad7a5c4" "Voting-Precincts-G22-prj" "$DATA_DIR/precincts_2022/Voting-Precincts-G22.prj"
download_file "9c79889f-57a5-4d53-84e8-cea0d1c05784" "Voting-Precincts-G22-sbn" "$DATA_DIR/precincts_2022/Voting-Precincts-G22.sbn"
download_file "1e5a0382-7ea9-4151-a0bd-0a7e45e2c50f" "Voting-Precincts-G22-sbx" "$DATA_DIR/precincts_2022/Voting-Precincts-G22.sbx"
download_file "66d06bfd-28f0-4f1b-9a1b-5e4b5aa7da49" "Voting-Precincts-G22-shp" "$DATA_DIR/precincts_2022/Voting-Precincts-G22.shp"
download_file "c4b60d33-e3c1-4b0c-be12-b8d79eef99ca" "Voting-Precincts-G22-shx" "$DATA_DIR/precincts_2022/Voting-Precincts-G22.shx"

# 2020 - Voting Precincts
echo "Downloading 2020 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2020"
download_file "f0dc3f15-6ebb-478f-b38b-0fdc1f9ee11d" "Voting-Precincts-G20-cpg" "$DATA_DIR/precincts_2020/Voting-Precincts-G20.cpg"
download_file "61f80e95-a37e-4ab0-9f26-8fc7ca1c9a75" "Voting-Precincts-G20-dbf" "$DATA_DIR/precincts_2020/Voting-Precincts-G20.dbf"
download_file "6acd9c88-49e4-49f5-af5f-e7fa41e6f29e" "Voting-Precincts-G20-prj" "$DATA_DIR/precincts_2020/Voting-Precincts-G20.prj"
download_file "77e13f99-ffda-4a38-9c62-ba2ca0866fb5" "Voting-Precincts-G20-sbn" "$DATA_DIR/precincts_2020/Voting-Precincts-G20.sbn"
download_file "1c7f638c-38ce-4ab8-9fcd-79dda0f36c5a" "Voting-Precincts-G20-sbx" "$DATA_DIR/precincts_2020/Voting-Precincts-G20.sbx"
download_file "d9eab30b-acb9-4b99-b652-9ec29d5e6c42" "Voting-Precincts-G20-shp" "$DATA_DIR/precincts_2020/Voting-Precincts-G20.shp"
download_file "f61bb4d7-41e8-4e34-934b-46e49bbb8258" "Voting-Precincts-G20-shx" "$DATA_DIR/precincts_2020/Voting-Precincts-G20.shx"

# 2018 - Voting Precincts
echo "Downloading 2018 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2018"
download_file "a7bd1f7b-ad8c-447f-88e1-bedb83d75fab" "Voting-Precincts-G18-cpg" "$DATA_DIR/precincts_2018/Voting-Precincts-G18.cpg"
download_file "15f6f7e1-8c26-4ca1-932f-4e05b12e5ff2" "Voting-Precincts-G18-dbf" "$DATA_DIR/precincts_2018/Voting-Precincts-G18.dbf"
download_file "f8edc39c-8efa-43e7-984a-2b0e2ae85752" "Voting-Precincts-G18-prj" "$DATA_DIR/precincts_2018/Voting-Precincts-G18.prj"
download_file "a5b1e2b9-b84f-4f4f-8089-e1ea26b5071b" "Voting-Precincts-G18-sbn" "$DATA_DIR/precincts_2018/Voting-Precincts-G18.sbn"
download_file "a5fc1c9b-b1ce-4cfc-bbd6-9b58c2f485dd" "Voting-Precincts-G18-sbx" "$DATA_DIR/precincts_2018/Voting-Precincts-G18.sbx"
download_file "97d9c476-df95-49dd-b2ea-d4ba09ea31b4" "Voting-Precincts-G18-shp" "$DATA_DIR/precincts_2018/Voting-Precincts-G18.shp"
download_file "cd10754d-1cb6-437f-ab5b-e02a3fe3f4ad" "Voting-Precincts-G18-shx" "$DATA_DIR/precincts_2018/Voting-Precincts-G18.shx"

# 2016 - Voting Precincts
echo "Downloading 2016 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2016"
download_file "f8a18802-2d09-42f5-8937-6e01eab37e9c" "Voting-Precincts-G16-cpg" "$DATA_DIR/precincts_2016/Voting-Precincts-G16.cpg"
download_file "27e1b2c2-8bd7-484f-ade8-25f2c6eab1e1" "Voting-Precincts-G16-dbf" "$DATA_DIR/precincts_2016/Voting-Precincts-G16.dbf"
download_file "38a9ebbf-3bb1-4e64-aa3d-7def16f32f16" "Voting-Precincts-G16-prj" "$DATA_DIR/precincts_2016/Voting-Precincts-G16.prj"
download_file "43b87fe2-e0b6-48e9-9f58-7afef0c50a8b" "Voting-Precincts-G16-sbn" "$DATA_DIR/precincts_2016/Voting-Precincts-G16.sbn"
download_file "3e903b4c-cc6f-4f07-929f-5d47c49a79f4" "Voting-Precincts-G16-sbx" "$DATA_DIR/precincts_2016/Voting-Precincts-G16.sbx"
download_file "4a033d37-bf77-4d10-a3cc-ce2c7c9cc5e9" "Voting-Precincts-G16-shp" "$DATA_DIR/precincts_2016/Voting-Precincts-G16.shp"
download_file "c4defd88-f5d9-4ec8-b2b9-20c0dafff862" "Voting-Precincts-G16-shx" "$DATA_DIR/precincts_2016/Voting-Precincts-G16.shx"

# 2014 - Precincts
echo "Downloading 2014 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2014"
download_file "c84d03bc-15e9-4fde-810a-bae6ab318c5d" "Precincts_G14-cpg" "$DATA_DIR/precincts_2014/Precincts_G14.cpg"
download_file "a4df61f7-ac6f-481b-aa99-eca29fa0fec4" "Precincts_G14-dbf" "$DATA_DIR/precincts_2014/Precincts_G14.dbf"
download_file "8cd6d92c-9e69-4a10-9f02-29ab34f8c929" "Precincts_G14-prj" "$DATA_DIR/precincts_2014/Precincts_G14.prj"
download_file "0d54cba7-92c7-4d08-a6a6-75c70dbc2bde" "Precincts_G14-sbn" "$DATA_DIR/precincts_2014/Precincts_G14.sbn"
download_file "6b8ed4e6-bce4-45eb-b89b-99e23cd42aec" "Precincts_G14-sbx" "$DATA_DIR/precincts_2014/Precincts_G14.sbx"
download_file "1d0038bb-a7c8-4e06-8f18-7e19a31e3ee1" "Precincts_G14-shp" "$DATA_DIR/precincts_2014/Precincts_G14.shp"
download_file "1ae50c2e-dd00-4f98-8d5b-9f0ea8ae4ca9" "Precincts_G14-shx" "$DATA_DIR/precincts_2014/Precincts_G14.shx"

# 2012 - Precincts
echo "Downloading 2012 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2012"
download_file "82bff6dc-a32d-428c-97fc-c04de1cf3e77" "Precincts_G12-dbf" "$DATA_DIR/precincts_2012/Precincts_G12.dbf"
download_file "b0ad05c1-f6fd-47cb-8502-f6b1a050aa6e" "Precincts_G12-prj" "$DATA_DIR/precincts_2012/Precincts_G12.prj"
download_file "ef86d3c9-cdb5-43cb-bd1a-09de0038929c" "Precincts_G12-sbn" "$DATA_DIR/precincts_2012/Precincts_G12.sbn"
download_file "ea7a8e42-eb82-4c3a-b850-3eefc69caa09" "Precincts_G12-sbx" "$DATA_DIR/precincts_2012/Precincts_G12.sbx"
download_file "7b2cde6f-1d5c-4a5e-abc8-d16ca39e1fd1" "Precincts_G12-shp" "$DATA_DIR/precincts_2012/Precincts_G12.shp"
download_file "ac9ff02d-5395-419f-8b31-73b6ba09f97d" "Precincts_G12-shx" "$DATA_DIR/precincts_2012/Precincts_G12.shx"

# 2010 - Precincts
echo "Downloading 2010 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2010"
download_file "32ef8343-2aef-4c45-863e-eb7088d2965f" "Precincts_G10-dbf" "$DATA_DIR/precincts_2010/Precincts_G10.dbf"
download_file "a8cac0c3-2d05-46ae-b4f4-c51ad28c0a7e" "Precincts_G10-prj" "$DATA_DIR/precincts_2010/Precincts_G10.prj"
download_file "e04e8d3f-a5c7-44a2-8e04-94de3de5fb37" "Precincts_G10-sbn" "$DATA_DIR/precincts_2010/Precincts_G10.sbn"
download_file "cf9f20a9-ea6f-4a12-9b6a-52f6c1308e71" "Precincts_G10-sbx" "$DATA_DIR/precincts_2010/Precincts_G10.sbx"
download_file "13bf24e3-7de6-492c-882c-03e5766a0be5" "Precincts_G10-shp" "$DATA_DIR/precincts_2010/Precincts_G10.shp"
download_file "a4d5ec04-cb17-4f5f-8a53-de89c9ef62dd" "Precincts_G10-shx" "$DATA_DIR/precincts_2010/Precincts_G10.shx"

# 2009 - Precincts P09
echo "Downloading 2009 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2009"
download_file "22d95b14-8bce-4bf8-b575-7a9800ea872b" "Precincts_P09-dbf" "$DATA_DIR/precincts_2009/Precincts_P09.dbf"
download_file "3985d815-1afd-4d1b-847a-cd36f7cce0a5" "Precincts_P09-prj" "$DATA_DIR/precincts_2009/Precincts_P09.prj"
download_file "e1434a1f-c17e-44d3-a5cb-d6b3fe78c5be" "Precincts_P09-sbn" "$DATA_DIR/precincts_2009/Precincts_P09.sbn"
download_file "078cf4f8-5288-400c-96bd-bb46259cf081" "Precincts_P09-sbx" "$DATA_DIR/precincts_2009/Precincts_P09.sbx"
download_file "c4855443-c67d-4ead-8092-f04b6ea6184a" "Precincts_P09-shp" "$DATA_DIR/precincts_2009/Precincts_P09.shp"
download_file "caaac57b-5aa1-4fd3-ae79-1c107a161c6d" "Precincts_P09-shx" "$DATA_DIR/precincts_2009/Precincts_P09.shx"

# 2008 - Precincts 08
echo "Downloading 2008 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2008"
download_file "fd71c636-ce38-4d51-9572-664a34611dca" "Precincts_08-dbf" "$DATA_DIR/precincts_2008/Precincts_08.dbf"
download_file "9b8c7621-696b-4bc4-ae9f-b3b50a3e4f3c" "Precincts_08-sbn" "$DATA_DIR/precincts_2008/Precincts_08.sbn"
download_file "6603a57e-a4ab-40da-9960-815b55e82d7f" "Precincts_08-sbx" "$DATA_DIR/precincts_2008/Precincts_08.sbx"
download_file "68580412-31b5-42d5-9bbc-8b62ce212dff" "Precincts_08-shp" "$DATA_DIR/precincts_2008/Precincts_08.shp"
download_file "dcd190e0-5271-49e9-bb81-9f1e67d2af09" "Precincts_08-shx" "$DATA_DIR/precincts_2008/Precincts_08.shx"

# 2007 - Precincts G07
echo "Downloading 2007 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2007"
download_file "e233a707-89bd-4003-b731-30a03cdda142" "Precincts_G07-dbf" "$DATA_DIR/precincts_2007/Precincts_G07.dbf"
download_file "6856100e-88a1-4245-882c-1ba2c366c77f" "Precincts_G07-prj" "$DATA_DIR/precincts_2007/Precincts_G07.prj"
download_file "cf8bc474-28f6-40fa-96c6-d7bf23c8d025" "Precincts_G07-sbn" "$DATA_DIR/precincts_2007/Precincts_G07.sbn"
download_file "3458ddc4-c029-47f4-9719-e8a818982fca" "Precincts_G07-sbx" "$DATA_DIR/precincts_2007/Precincts_G07.sbx"
download_file "f066e549-964f-4cfc-97bd-769a4fdb6b44" "Precincts_G07-shp" "$DATA_DIR/precincts_2007/Precincts_G07.shp"
download_file "365f713a-387e-48a8-8e8e-6bc8fb77337a" "Precincts_G07-shx" "$DATA_DIR/precincts_2007/Precincts_G07.shx"

# 2006 - Precincts G06
echo "Downloading 2006 shapefiles..."
mkdir -p "$DATA_DIR/precincts_2006"
download_file "82289fcd-f7a0-465d-beac-c4997c9acb81" "Precincts_G06-dbf" "$DATA_DIR/precincts_2006/Precincts_G06.dbf"
download_file "ade46e5c-ecdc-4ad5-b877-860804a904b6" "Precincts_G06-sbn" "$DATA_DIR/precincts_2006/Precincts_G06.sbn"
download_file "3ccb325a-f871-4e62-801e-6431ad4919d1" "Precincts_G06-sbx" "$DATA_DIR/precincts_2006/Precincts_G06.sbx"
download_file "2eca4be0-e2b2-49c9-9902-88a82fdc764b" "Precincts_G06-shp" "$DATA_DIR/precincts_2006/Precincts_G06.shp"
download_file "df0621d0-925a-480d-ba6c-2546e2a46d66" "Precincts_G06-shx" "$DATA_DIR/precincts_2006/Precincts_G06.shx"

echo ""
echo "=========================================="
echo "Download complete!"
echo "=========================================="
echo ""
echo "Shapefiles organized in:"
echo "  data/raw/precincts_YYYY/"
echo ""
echo "Years downloaded: 2006-2025"
echo ""
