from app.extractors.coordinate_extractor import extract_coordinates


def test_single_coordinate_with_seconds():
    html = """
    <span class="geo-inline">
      <a class="external text" href="https://geohack.toolforge.org/geohack.php?pagename=Mount_Everest&params=27_59_18_N_86_55_31_E_type:mountain">
        <span class="geo-dms">
          <span class="latitude">27°59′18″N</span>
          <span class="longitude">86°55′31″E</span>
        </span>
      </a>
    </span>
    """

    locations = extract_coordinates(html, article_title="Mount Everest")

    assert len(locations) == 1
    loc = locations[0]
    assert loc.name == "Mount Everest"
    assert round(loc.latitude, 4) == 27.9883
    assert round(loc.longitude, 4) == 86.9253


def test_coordinate_without_seconds():
    html = """
    <span class="latitude">57°18′N</span>
    <span class="longitude">6°21′W</span>
    """

    locations = extract_coordinates(html, article_title="Isle of Skye")

    assert len(locations) == 1
    assert round(locations[0].latitude, 2) == 57.30
    assert round(locations[0].longitude, 2) == -6.35  # W -> отрицательное значение


def test_southern_and_western_hemisphere_are_negative():
    html = """
    <span class="latitude">2°19′35″S</span>
    <span class="longitude">29°21′30″W</span>
    """

    locations = extract_coordinates(html, article_title="Test")

    assert locations[0].latitude < 0
    assert locations[0].longitude < 0


def test_multiple_coordinates_with_titles_from_geohack():
    html = """
    <a class="external text" href="https://geohack.toolforge.org/geohack.php?pagename=Seven_Summits&params=27.9881_N_86.925_E_&title=Mount+Everest+%288848.86+m%29">
      <span class="latitude">27°59′17″N</span>
      <span class="longitude">86°55′30″E</span>
    </a>
    <a class="external text" href="https://geohack.toolforge.org/geohack.php?pagename=Seven_Summits&params=32.6531_S_70.0117_W_&title=Aconcagua+%286962+m%29">
      <span class="latitude">32°39′11″S</span>
      <span class="longitude">70°00′42″W</span>
    </a>
    """

    locations = extract_coordinates(html, article_title="Seven Summits")

    assert len(locations) == 2
    assert locations[0].name == "Mount Everest"
    assert locations[1].name == "Aconcagua"


def test_coordinate_ids_are_sequential():
    html = """
    <span class="latitude">1°N</span><span class="longitude">1°E</span>
    <span class="latitude">2°N</span><span class="longitude">2°E</span>
    """

    locations = extract_coordinates(html, article_title="Test")

    assert locations[0].id == "location-0"
    assert locations[1].id == "location-1"


def test_no_coordinates_returns_empty_list():
    assert extract_coordinates("<p>No coordinates here.</p>", article_title="Test") == []


def test_empty_html_returns_empty_list():
    assert extract_coordinates("", article_title="Test") == []


def test_mismatched_lat_lon_count_uses_shorter():
    # Если по какой-то причине latitude и longitude spans не совпадают по числу,
    # zip() останавливается на более коротком списке — не должно упасть.
    html = """
    <span class="latitude">1°N</span>
    <span class="latitude">2°N</span>
    <span class="longitude">1°E</span>
    """

    locations = extract_coordinates(html, article_title="Test")

    assert len(locations) == 1

def test_duplicate_coordinates_are_removed():
    html = """
    <span class="latitude">27°59′18″N</span>
    <span class="longitude">86°55′31″E</span>

    <span class="latitude">27°59′18″N</span>
    <span class="longitude">86°55′31″E</span>

    <span class="latitude">32°39′11″S</span>
    <span class="longitude">70°00′42″W</span>
    """

    locations = extract_coordinates(html, article_title="Test")

    assert len(locations) == 2  # дубликат убран, осталось два уникальных

def test_russian_coordinates_basic():
    html = """
    <span class="coordinates">
        <span>35°42′ с.ш. 139°36′ в.д.</span>
    </span>
    """

    locations = extract_coordinates(html, article_title="Токио")

    assert len(locations) == 1
    assert locations[0].name == "Токио"
    assert round(locations[0].latitude, 2) == 35.70
    assert round(locations[0].longitude, 2) == 139.60


def test_russian_coordinates_with_seconds():
    html = """
    <span class="coordinates">
        <span>27°59′17″ с.ш. 86°55′31″ в.д.</span>
    </span>
    """

    locations = extract_coordinates(html, article_title="Джомолунгма")

    assert round(locations[0].latitude, 4) == 27.9881
    assert round(locations[0].longitude, 4) == 86.9253


def test_russian_coordinates_south_and_west_are_negative():
    html = """
    <span class="coordinates">
        <span>2°19′ ю.ш. 29°21′ з.д.</span>
    </span>
    """

    locations = extract_coordinates(html, article_title="Test")

    assert locations[0].latitude < 0
    assert locations[0].longitude < 0


def test_russian_coordinates_name_always_from_article_title():
    html = """
    <span class="coordinates"><span>48°50′ с.ш. 2°20′ в.д.</span></span>
    <span class="coordinates"><span>45°45′ с.ш. 4°51′ в.д.</span></span>
    """

    locations = extract_coordinates(html, article_title="Франция")

    assert len(locations) == 2
    assert all(loc.name == "Франция" for loc in locations)


def test_english_and_russian_paths_both_work_independently():
    html = """
    <span class="latitude">10°N</span><span class="longitude">10°E</span>
    <span class="coordinates"><span>20°с.ш. 20°в.д.</span></span>
    """

    locations = extract_coordinates(html, article_title="Test")

    assert len(locations) == 2