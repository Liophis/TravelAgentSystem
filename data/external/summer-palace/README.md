# Summer Palace External Map Payloads

Raw downloaded source payloads for `scene_key=summer_palace`.

Expected files:

```text
osm/osmnx_summer_palace_payload.json
amap_gcj02/food_pois_raw.json
```

Optional recommended file:

```text
amap_gcj02/summer_palace_pois_raw.json
```

Generate the optional scenic/service POI payload with:

```bash
bash scripts/download_summer_palace_pois.sh
```

Current OSMnx payload counts:

```text
nodes: 236
edges: 630
buildings/scenic structures: 228
facilities/POIs: 79
```

Current AMap food payload counts:

```text
raw food POIs: 343
clean imported restaurants: 202
```

These files are third-party source captures. Import them through backend scripts before API runtime use.

Data policy:

- OSMnx/OpenStreetMap is used for the Summer Palace road graph and scenic/building polygons.
- AMap Place Around should be used for user-facing scenic/service POIs when the raw payload is available.
- When the general scenic/service POI payload is not present, the existing AMap food payload can be imported into the facilities layer as real restaurant/cafe/fast-food service POIs.
- Generic low-value OSM facilities such as `bench` are removed by navigation data cleanup.
