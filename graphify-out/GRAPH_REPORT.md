# Graph Report - .  (2026-07-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 867 nodes · 1552 edges · 52 communities (42 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 106 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `04e63799`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.py
- app/main.py
- app.js
- targetFlight
- notam_server.py
- test_chat_tool_groups.py
- dependencies
- sondehub_server.py
- global_tools.py
- compilerOptions
- astra_server.py
- flight
- simulator.py
- environment
- GFS_Handler
- test_web_app.py
- package.json
- GFS.py
- Header.tsx
- forecastEnvironment
- weather.py
- DummyEnvironment
- .write
- mcp_bridge.py
- weather_server.py
- GFS_Map
- flightProfile
- MessageList.tsx
- chat.ts
- llm.py
- chat/page.tsx
- get_surface_weather
- TrajectoryArtifactMap.tsx
- GFS_data_interpolator
- test_flight.py
- InputBar.tsx
- OpenAIProvider
- get_tools
- app/layout.tsx
- extends
- chat/layout.tsx
- app/__init__.py
- hab_predictor/__init__.py
- vendor/__init__.py
- eslint.config.mjs
- next.config.mjs

## God Nodes (most connected - your core abstractions)
1. `flight` - 36 edges
2. `run_simulation()` - 27 edges
3. `GFS_Handler` - 27 edges
4. `FakeProvider` - 22 edges
5. `targetFlight` - 21 edges
6. `FakeCompletions` - 19 edges
7. `wireEvents()` - 19 edges
8. `forecastEnvironment` - 18 edges
9. `_compute_balloon_no_flight_zone()` - 17 edges
10. `Linear4DInterpolator` - 17 edges

## Surprising Connections (you probably didn't know these)
- `test_invalid_inputs()` --calls--> `flight`  [INFERRED]
  backend/vendor/hab_predictor/test/test_flight.py → backend/vendor/hab_predictor/astra/simulator.py
- `_compute_balloon_no_flight_zone()` --calls--> `get_settings()`  [INFERRED]
  backend/mcp_servers/notam_server.py → backend/app/config.py
- `chat()` --calls--> `execute_tool()`  [INFERRED]
  backend/app/main.py → backend/llm.py
- `chat()` --calls--> `OpenAIProvider`  [INFERRED]
  backend/app/main.py → backend/llm.py
- `test_raw_string_tool_output_quarantine_is_deterministic()` --calls--> `format_tool_output_message()`  [INFERRED]
  backend/tests/test_prompt_assembly.py → backend/app/prompt_assembly.py

## Import Cycles
- None detected.

## Communities (52 total, 10 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.11
Nodes (55): _aggregate_runs(), _apply_sondehub_calibration(), _build_mean_location(), _build_mean_trajectory(), _build_sondehub_artifact_reference(), _build_sondehub_calibration(), _build_sondehub_comparison(), _build_sondehub_reference() (+47 more)

### Community 1 - "app/main.py"
Cohesion: 0.08
Nodes (43): chat(), _is_tool_continuation_response(), _llm_usage_to_dict(), _normalise_confirmation_text(), _parse_chat_request(), McpToolGroupId, Return only enabled tool groups that are relevant to this chat turn., _read_limited_body() (+35 more)

### Community 2 - "app.js"
Cohesion: 0.12
Nodes (49): boot(), buildUtcLaunchTimestamp(), createDivIcon(), currentFormPayload(), DEFAULT_LAUNCH, drawSimulation(), ensureLaunchMarker(), estimateLift() (+41 more)

### Community 3 - "targetFlight"
Cohesion: 0.06
Nodes (31): balloonDrag(), density(), gasMassForFloat(), liftingGasMass(), nozzleLiftFixedAscent(), nozzleLiftForFloat(), parachuteDrag(), Returns the gas mass profile to simulate the valves venting air to reach     flo (+23 more)

### Community 4 - "notam_server.py"
Cohesion: 0.13
Nodes (41): _bbox_intersects(), _bbox_polygon(), _build_corridor_context(), _build_no_flight_zone_geometry(), _build_summary(), _call_gairmet(), _call_laminar_restrictions(), _call_sigmet() (+33 more)

### Community 5 - "test_chat_tool_groups.py"
Cohesion: 0.11
Nodes (26): assert_untrusted_message(), decode_envelope(), FakeCompletions, FakeProvider, make_message(), make_tool_call(), test_active_loop_model_tool_calls_remain_authoritative(), test_chat_accepts_boundary_message_and_history() (+18 more)

### Community 6 - "dependencies"
Cohesion: 0.05
Nodes (38): eslint, eslint-config-next, dependencies, leaflet, next, react, react-dom, react-leaflet (+30 more)

### Community 7 - "sondehub_server.py"
Cohesion: 0.18
Nodes (30): _aggregate_runs(), _build_mean_trajectory(), _build_run_summary(), _build_sampled_requests(), _datetime_to_rfc3339_utc(), _error_payload(), _fetch_sondehub_prediction(), _great_circle_km() (+22 more)

### Community 8 - "global_tools.py"
Cohesion: 0.08
Nodes (28): c2kel(), deg2m(), dirspeed2uv(), feet2m(), find_nearest_index(), getUTCOffset(), haversine(), ISAatmosphere() (+20 more)

### Community 9 - "compilerOptions"
Cohesion: 0.07
Nodes (27): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+19 more)

### Community 10 - "astra_server.py"
Cohesion: 0.12
Nodes (15): get_settings(), Settings, astra_calculate_balloon_volume(), astra_calculate_nozzle_lift(), astra_list_balloons(), astra_list_parachutes(), astra_run_simulation(), BalloonVolumeInput (+7 more)

### Community 11 - "flight"
Cohesion: 0.09
Nodes (13): flight, Primary Balloon flight simulation class.      Provides methods for solving the a, Initialize all the parameters of the object and setup the debugging if         r, Sampling time property          Note: No setter exists for this, as it should no, launch site latitiude property, launch site longitude property, balloon gas type property (string)          Also updates the molecular mass attr, balloon model property (string)                  Setting this value also updates (+5 more)

### Community 12 - "simulator.py"
Cohesion: 0.11
Nodes (8): NullHandler, # TODO: Make highestAltitude and highestAltIndex calculated on, interpIndividual(), Converts normalised values contained within the individual     (python iterable), example_forecast.py ASTRA High Altitude Balloon Flight Planner  DESCRIPTION ----, example_forecast.py ASTRA High Altitude Balloon Flight Planner  DESCRIPTION ----, Example Sounding based Simulation  ASTRA High Altitude Balloon Flight Planner  U, # TODO: Add an example sounding file, with description of how to create one

### Community 13 - "environment"
Cohesion: 0.11
Nodes (13): environment, object, Request the temperature for an input location and time.          Returns, request the pressure for the point at the given location at the         given ti, request the density for the point at the given location at the         given tim, getViscosity(): request the viscosity for the point         at the given locatio, request the wind speed for the point at the given location at the         given, getWindDirection(lat,lon,alt,time): request the wind direction for         the p (+5 more)

### Community 14 - "GFS_Handler"
Cohesion: 0.15
Nodes (10): GFS_Handler, Parameters         ----------         requestVar : string             noaa ident, Downloads data from a NOAA request url, before generating the         matrix and, Requests temperature, altitude and U-V wind direction data from the         NOAA, Collects all urls for noaa data requests for parameters in         self.weatherP, For an input cycle, this function will load all weather variables.          Mult, Makes multiple attempts to find an available data set (cycle) from         the n, Connect to the Global Forecast System and download the closest cycle         ava (+2 more)

### Community 15 - "test_web_app.py"
Cohesion: 0.14
Nodes (9): FakeProfile, _open_meteo_payload(), _read_fixture(), test_apply_sondehub_calibration_recenters_path_without_moving_launch(), test_build_sondehub_calibration_reports_raw_vs_reference_delta(), test_estimate_sondehub_request_uses_baseline_rates(), test_generate_matrix_parses_thredds_time1(), test_generate_matrix_parses_thredds_time_coordinate() (+1 more)

### Community 16 - "package.json"
Cohesion: 0.11
Nodes (18): author, bugs, url, description, directories, doc, homepage, keywords (+10 more)

### Community 17 - "GFS.py"
Cohesion: 0.13
Nodes (10): get_urldict_async(), GFS_High_Altitude_Handler, # TODO: Migrate this class back to GFS_Handler - there is no need for an, # NOTE: Grid sizes are defined as the difference between the highest, An asynchronous helper function for making multiple url requests per     key in, # TODO: Fix this unreadable line: Is it trying to get the earliest, Linear4DInterpolator, object (+2 more)

### Community 18 - "Header.tsx"
Cohesion: 0.14
Nodes (6): HeaderProps, Tab, TABS, SidebarProps, Mission, MissionStatus

### Community 20 - "forecastEnvironment"
Cohesion: 0.13
Nodes (9): environment property, subclass of :obj:`astra.weather.environment`          Will, Extends the astra.simulator.flightProfile to assign both a fitness     measure,, targetProfile, forecastEnvironment, Perform a wind perturbation for the purpose of Monte Carlo simulations., Initialize the soundingEnvironment object.          See class documentation., Class responsible for downloading weather forecast data from the Global     Fore, Initialize the forecastEnvironment object (+1 more)

### Community 21 - "weather.py"
Cohesion: 0.15
Nodes (8): # TODO: MODIFY HERE TO ADD WIND PERTURBATION TO FORECAST, Class for generating an atmospheric model from sounding data.      Instantiate a, # TODO: Fix this part, it's unreadable and difficult to debug, Constructor function responsible for applying perturbations to wind, Perturb the wind profiles for the purpose of Monte Carlo simulations.          G, soundingEnvironment, This roughly runs the sounding example and performs some primitive     assertion, test_soundingEnvironment()

### Community 22 - "DummyEnvironment"
Cohesion: 0.15
Nodes (7): DummyEnvironment, DummyResponse, FakeGFSModule, object, RefreshingEnvironment, test_fetch_open_meteo_uses_correct_wind_variable_names(), test_forecast_cache_refreshes_when_actual_cycle_lags_latest()

### Community 23 - ".write"
Cohesion: 0.16
Nodes (7): GENERATE CSV FILE OUT OF RESULTS, Function responsible for storing the data contained in self.results         in t, After all the simulations have been executed, this method puts the         resul, Update the progress file with the ratio of value and the total steps of, This method takes all the necessary steps to run the simulation and         wrap, Run a series of pre-flight checks and calculations to verify the         consist, Execute a single simulation.         It should be run N times, where N is the nu

### Community 24 - "mcp_bridge.py"
Cohesion: 0.33
Nodes (13): _balloon_catalog_by_name(), _balloon_catalog_markdown(), _calculate_balloon_volume(), _calculate_nozzle_lift(), _configure_runtime(), _dispatch(), _emit_stdout_line(), main() (+5 more)

### Community 25 - "weather_server.py"
Cohesion: 0.28
Nodes (12): get_winds_aloft(), _nearest_forecast_index(), _normalise_dt(), _obs_links(), _parse_forecast_datetime(), _parse_open_meteo_time(), datetime, Weather MCP server — Surface weather + Winds aloft.  Can be run as a standalone (+4 more)

### Community 26 - "GFS_Map"
Cohesion: 0.19
Nodes (7): GFS_Map, Private class used to store 4D mapping data for a specific parameter.      Note:, This method joins and returns this map and the one passed in         data_map, c, Prepare the mappingCoordinates variable by putting together all         forward, Parameters         ----------         fileDict : :obj:`dict`             A dicti, Generates data matrices and coordinates mapping.          Called by the download, test_pressure_interpolator_handles_ascending_thredds_pressures()

### Community 27 - "flightProfile"
Cohesion: 0.18
Nodes (5): flightProfile, object, GENERATE KML OUT OF RESULTS          Also allows zipped kml (kmz) if .kmz is pro, Creates a new profile, which is a new instance of this profile, with         add, Parameters     ----------     launchDateTime : datetime.datetime         The tim

### Community 28 - "MessageList.tsx"
Cohesion: 0.18
Nodes (8): AssistantMessage(), formatUtcTime(), getArgSummary(), LOADING_STEPS, MessageListProps, TOOL_LABELS, ToolCallsSection(), TrajectoryArtifactMap

### Community 29 - "chat.ts"
Cohesion: 0.25
Nodes (7): MessageRole, RestrictionIntersection, RestrictionOverlay, SondehubRequestSummary, SondehubTrajectoryReference, ToolCallRecord, TrajectoryArtifactPoint

### Community 30 - "llm.py"
Cohesion: 0.22
Nodes (7): execute_tool(), LLMProvider, _normalize_tool_result(), Any, LLM provider abstraction, OpenAI implementation.  Exports:   ALL_TOOLS, merged O, Normalize tool output into JSON-serializable data., Execute any named tool and return a JSON string result.

### Community 31 - "chat/page.tsx"
Cohesion: 0.22
Nodes (9): ChatPage(), generateId(), SUGGESTIONS, ChatApiResponse, getChatEndpoint(), sendMessage(), MISSIONS, Message (+1 more)

### Community 32 - "get_surface_weather"
Cohesion: 0.22
Nodes (9): _assess_hour(), _call_open_meteo(), get_surface_weather(), Any, Return 'NO-GO: <reasons>', 'CAUTION: <reasons>', or 'GO' for one hour., Fetch surface weather and GO/CAUTION/NO-GO assessment for a launch site.      Ar, Return lst[i] or default when out-of-range or None., Call Open-Meteo; raise httpx.HTTPStatusError on non-2xx. (+1 more)

### Community 33 - "TrajectoryArtifactMap.tsx"
Cohesion: 0.33
Nodes (7): formatDebugNumber(), formatPoint(), geometryPositions(), overlayStyle(), RestrictionGeometryLayer(), TrajectoryArtifactMap(), RestrictionGeometry

### Community 34 - "GFS_data_interpolator"
Cohesion: 0.25
Nodes (5): GFS_data_interpolator, object, Extracts pressure from (lat,lon,alt,time) coordinates.          This is essentia, Private class used by GFS_Handler to interpolate data.      This class acts as a, Set up a linear 4d interpolation for each variable given and returns         it.

### Community 35 - "test_flight.py"
Cohesion: 0.29
Nodes (6): example_inputs(), # TODO: Add more checks here to compare the path obtained with a reference, Initializes a standard set of inputs to the flight class and injects     a reque, Note: this test is extremely minimal, and only checks if a solution is     simil, test_forecast_example_inputs(), test_invalid_inputs()

### Community 38 - "get_tools"
Cohesion: 0.40
Nodes (3): get_tools(), McpToolGroupId, Return tool schemas filtered by enabled MCP group ids.

## Knowledge Gaps
- **80 isolated node(s):** `state`, `DEFAULT_LAUNCH`, `next/core-web-vitals`, `config`, `nextConfig` (+75 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `flight` connect `flight` to `app.py`, `targetFlight`, `test_flight.py`, `simulator.py`, `forecastEnvironment`, `weather.py`, `.write`, `flightProfile`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Why does `GFS_Handler` connect `GFS_Handler` to `GFS_data_interpolator`, `test_web_app.py`, `GFS.py`, `DummyEnvironment`, `GFS_Map`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `forecastEnvironment` connect `forecastEnvironment` to `app.py`, `targetFlight`, `test_flight.py`, `flight`, `simulator.py`, `environment`, `weather.py`, `flightProfile`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `flight` (e.g. with `run_simulation()` and `forecastEnvironment`) actually correct?**
  _`flight` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `run_simulation()` (e.g. with `flight` and `forecastEnvironment`) actually correct?**
  _`run_simulation()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `GFS_Handler` (e.g. with `Linear4DInterpolator` and `DummyEnvironment`) actually correct?**
  _`GFS_Handler` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `state`, `DEFAULT_LAUNCH`, `next/core-web-vitals` to the rest of the system?**
  _80 weakly-connected nodes found - possible documentation gaps or missing edges._