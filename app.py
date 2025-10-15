"""
Streamlit WordPress REST Explorer
- Paste a site URL (e.g. https://videmiservices.com)
- Click "Fetch API root" to enumerate namespaces & routes from /wp-json/
- Click any route to fetch its JSON; supports basic pagination for wp/v2 endpoints
- Convert common collection endpoints to a table and download as CSV
Notes:
- Respect site permissions and rate-limits. Don't scan sites without authorization.
"""

from urllib.parse import urljoin, urlparse
import json
import time
import re

import requests
import pandas as pd
import streamlit as st
from requests.exceptions import RequestException

st.set_page_config(page_title="WP REST Explorer", layout="wide")

# -----------------------
# Utility functions
# -----------------------
@st.cache_data(ttl=300)
def normalize_base(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
    # remove trailing slash
    return url.rstrip("/")

def api_root_url(base_url: str) -> str:
    return normalize_base(base_url) + "/wp-json/"

@st.cache_data(ttl=300)
def fetch_url(url: str, headers=None, cookies=None, timeout=10):
    try:
        resp = requests.get(url, headers=headers or {}, cookies=cookies or {}, timeout=timeout)
        return resp
    except RequestException as e:
        return e

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        # fallback: try to pretty print text
        try:
            return json.loads(resp.text)
        except Exception:
            return None

def is_collection_route(route: str):
    # heuristic: wp/v2 endpoints that usually return lists
    return bool(re.search(r"/wp/v2/(posts|pages|media|categories|tags|comments|users|taxonomies)", route))

def join_api(base, route):
    # route may start with / or not; route may already include /wp-json
    if route.startswith("/wp-json/"):
        return normalize_base(base) + route[len("/wp-json"):]
    if route.startswith("/"):
        return normalize_base(base) + "/wp-json" + route
    # if route already looks full:
    if route.startswith("http://") or route.startswith("https://"):
        return route
    return normalize_base(base) + "/wp-json/" + route.lstrip("/")

# -----------------------
# UI: Sidebar (settings)
# -----------------------
st.sidebar.title("WP REST Explorer")
site_input = st.sidebar.text_input("Site URL", value="https://videmiservices.com")
auth_method = st.sidebar.selectbox("Auth / Access", ["None", "Bearer token", "Basic auth", "Cookie (session)"])
token = None
basic_auth = None
cookies = None

if auth_method == "Bearer token":
    token = st.sidebar.text_input("Bearer token", type="password")
elif auth_method == "Basic auth":
    user = st.sidebar.text_input("Username")
    pwd = st.sidebar.text_input("Password", type="password")
    if user and pwd:
        basic_auth = (user, pwd)
elif auth_method == "Cookie (session)":
    cookie_str = st.sidebar.text_area("Cookies (name=value; separate with ; )", help="Paste cookies from browser if site uses session auth")
    if cookie_str:
        cookies = {}
        for part in cookie_str.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                cookies[k.strip()] = v.strip()

# extra headers
extra_headers_raw = st.sidebar.text_area("Extra headers (JSON)", value='{}', help='e.g. {"X-Requested-With": "XMLHttpRequest"}')
try:
    extra_headers = json.loads(extra_headers_raw or "{}")
except Exception:
    extra_headers = {}
if token:
    extra_headers["Authorization"] = f"Bearer {token}"

# options
st.sidebar.markdown("---")
st.sidebar.write("Fetch options")
per_page_default = st.sidebar.number_input("per_page (for paginated endpoints)", min_value=1, max_value=100, value=20)
delay = st.sidebar.number_input("Delay between requests (s)", min_value=0.0, max_value=5.0, value=0.2, step=0.1)
st.sidebar.caption("Tip: If /wp-json/ returns 401/403 you may need credentials or cookies.")

# -----------------------
# Main layout
# -----------------------
col_left, col_right = st.columns([1, 2])

with col_left:
    st.header("API Root")
    st.write("Base site:", normalize_base(site_input))
    if st.button("Fetch /wp-json/"):
        root = api_root_url(site_input)
        headers = extra_headers.copy()
        # Basic auth support
        try:
            if basic_auth:
                resp = requests.get(root, headers=headers, auth=basic_auth, cookies=cookies or {}, timeout=10)
            else:
                resp = requests.get(root, headers=headers, cookies=cookies or {}, timeout=10)
        except RequestException as e:
            st.error(f"Request failed: {e}")
            resp = None

        if not resp:
            st.stop()

        if isinstance(resp, requests.Response):
            st.write("Status:", resp.status_code)
            if resp.status_code == 200:
                try:
                    root_json = resp.json()
                    st.success("Root fetched successfully.")
                    st.session_state["root_json"] = root_json
                except Exception:
                    st.warning("Root responded but couldn't parse JSON.")
                    st.session_state["root_text"] = resp.text
            else:
                st.error(f"Fetching root returned {resp.status_code}. Response snippet:")
                st.code(resp.text[:600])
        else:
            st.error("Unexpected response.")

    # show cached root (if any)
    root_json = st.session_state.get("root_json")
    if root_json:
        st.subheader("Namespaces")
        namespaces = root_json.get("namespaces", [])
        st.write(", ".join(namespaces) if namespaces else "No namespaces found.")
        st.subheader("Routes (summary)")
        routes = root_json.get("routes", {})
        # Show a short table of routes
        rows = []
        for r, info in routes.items():
            rows.append({
                "route": r,
                "methods": ",".join(info.get("methods", [])) if isinstance(info.get("methods"), list) else str(info.get("methods")),
                "endpoints": info.get("endpoints", [{}])[0].get("args", None) is not None
            })
        df_routes = pd.DataFrame(rows)
        st.dataframe(df_routes.head(200), use_container_width=True)
        # store routes in session
        st.session_state["routes"] = routes

    else:
        st.info("No root loaded yet. Click 'Fetch /wp-json/' to enumerate the REST API.")

    st.markdown("---")
    st.subheader("Quick route tester")
    route_input = st.text_input("Route (relative to /wp-json/) e.g. wp/v2/posts", value="wp/v2/posts")
    params_raw = st.text_input("Query params (e.g. ?per_page=10&page=1 or id=5&context=edit)", value="")
    full_example = join_api(site_input, route_input) + (("?" + params_raw.lstrip("?")) if params_raw else "")
    st.caption("Full URL: " + full_example)
    if st.button("Fetch route"):
        url = join_api(site_input, route_input)
        if params_raw:
            if params_raw.strip().startswith("?"):
                url = url + params_raw.strip()
            else:
                url = url + "?" + params_raw.strip()
        headers = extra_headers.copy()
        try:
            if basic_auth:
                resp = requests.get(url, headers=headers, auth=basic_auth, cookies=cookies or {}, timeout=15)
            else:
                resp = requests.get(url, headers=headers, cookies=cookies or {}, timeout=15)
        except RequestException as e:
            st.error(f"Error fetching {url}: {e}")
            st.stop()
        st.write("Status:", resp.status_code)
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type or resp.text.strip().startswith("{") or resp.text.strip().startswith("["):
            try:
                j = resp.json()
                st.session_state["last_json"] = j
                st.json(j)
            except Exception:
                st.code(resp.text[:1000])
        else:
            st.code(resp.text[:2000])

with col_right:
    st.header("Explorer & Tools")
    # show routes list from session
    routes = st.session_state.get("routes", {})
    if routes:
        st.subheader("All available routes")
        # present as expandable groups by namespace
        grouped = {}
        for r, info in routes.items():
            ns = r.split("/")[1] if r.startswith("/") and len(r.split("/")) > 1 else "root"
            grouped.setdefault(ns, []).append((r, info))
        for ns, items in grouped.items():
            with st.expander(f"{ns} — {len(items)} routes", expanded=False):
                # list clickable buttons for first 100 routes
                for r, info in items[:400]:
                    col_a, col_b = st.columns([6, 1])
                    col_a.write(f"`{r}` — methods: {','.join(info.get('methods',[])) if isinstance(info.get('methods',[]), list) else info.get('methods')}")
                    if col_b.button("Open", key=f"open_{r}"):
                        # load route into quick tester input fields
                        st.session_state["selected_route"] = r
                        st.session_state["selected_route_info"] = info
                        st.experimental_rerun()
    else:
        st.info("No routes found — fetch API root first.")

    st.markdown("---")
    # If a route selected, show fetch & pagination helpers
    selected_route = st.session_state.get("selected_route", None)
    if selected_route:
        st.subheader("Selected route")
        st.write("Route:", selected_route)
        info = st.session_state.get("selected_route_info", {})
        st.write("Methods:", info.get("methods"))
        st.write("Description:", info.get("description", ""))
        # show parameter hints
        args = info.get("endpoints", [{}])[0].get("args", {})
        if args:
            st.write("Arguments available:")
            for k, v in args.items():
                st.write(f"- `{k}` : {v.get('description','')}")
        # controls
        if is_collection_route(selected_route):
            st.info("This looks like a collection route — pagination controls available.")
            per_page = st.number_input("per_page", min_value=1, max_value=100, value=per_page_default, key="per_page_input")
            max_pages = st.number_input("max pages to fetch (stop after)", min_value=1, max_value=100, value=3)
            if st.button("Fetch all pages"):
                base = normalize_base(site_input)
                # iterate pages
                all_items = []
                headers = extra_headers.copy()
                page = 1
                while True:
                    url = join_api(site_input, selected_route)
                    sep = "&" if "?" in url else "?"
                    full_url = f"{url}{sep}per_page={per_page}&page={page}"
                    try:
                        if basic_auth:
                            resp = requests.get(full_url, headers=headers, auth=basic_auth, cookies=cookies or {}, timeout=20)
                        else:
                            resp = requests.get(full_url, headers=headers, cookies=cookies or {}, timeout=20)
                    except RequestException as e:
                        st.error(f"Request error: {e}")
                        break
                    st.write(f"Page {page} — status {resp.status_code} — items: {len(resp.text) if resp.text else 0}")
                    if resp.status_code != 200:
                        break
                    try:
                        chunk = resp.json()
                    except Exception:
                        st.warning("Failed to parse JSON for page " + str(page))
                        break
                    if not isinstance(chunk, list) or len(chunk) == 0:
                        # sometimes single item or empty
                        if page == 1 and isinstance(chunk, dict):
                            all_items = [chunk]
                        break
                    all_items.extend(chunk)
                    page += 1
                    if page > max_pages:
                        st.warning("Reached max_pages limit.")
                        break
                    time.sleep(delay)
                st.success(f"Fetched total items: {len(all_items)}")
                st.session_state["last_collection"] = all_items
                # display table preview (flatten)
                try:
                    df = pd.json_normalize(all_items)
                    st.dataframe(df.head(200), use_container_width=True)
                    # offer CSV
                    csv = df.to_csv(index=False)
                    st.download_button("Download CSV", csv, file_name=f"{selected_route.strip('/').replace('/','_')}.csv", mime="text/csv")
                except Exception as e:
                    st.warning("Couldn't convert to table: " + str(e))
                    st.json(all_items[:50])
        else:
            st.write("Non-collection route. Use the 'Fetch route' button on the left to test arbitrary parameters.")

    # show last fetched json (single)
    last_json = st.session_state.get("last_json")
    if last_json:
        st.markdown("### Last fetched JSON (preview)")
        st.json(last_json)
        if st.button("Download last JSON"):
            st.download_button("Download JSON", json.dumps(last_json, indent=2), file_name="wp_last.json", mime="application/json")

    last_collection = st.session_state.get("last_collection")
    if last_collection:
        st.markdown("### Last fetched collection")
        st.write(f"Items: {len(last_collection)}")
        try:
            df = pd.json_normalize(last_collection)
            st.dataframe(df.head(500), use_container_width=True)
            csv = df.to_csv(index=False)
            st.download_button("Download collection CSV", csv, file_name="collection.csv", mime="text/csv")
        except Exception:
            st.json(last_collection[:200])

st.markdown("---")
st.caption("Built with ❤️ — remember to obtain permission before enumerating private endpoints.")
