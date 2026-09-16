from app.extractors.image_extractor import extract_images


def test_body_illustration_with_simple_caption():
    html = """
    <div class="thumb">
        <div class="thumbinner">
            <a href="/wiki/File:Example.jpg" class="mw-file-description">
                <img src="//upload.wikimedia.org/thumb/example/330px-Example.jpg" alt="An example" />
            </a>
            <div class="thumbcaption">A simple caption</div>
        </div>
    </div>
    """

    images = extract_images(html)

    assert len(images) == 1
    assert images[0].caption == "A simple caption"
    assert images[0].alt == "An example"
    assert images[0].thumbnail_url == "https://upload.wikimedia.org/thumb/example/330px-Example.jpg"
    assert images[0].url == "https://upload.wikimedia.org/thumb/example/1280px-Example.jpg"


def test_caption_with_link_gets_space_separated():
    html = """
    <div class="thumb">
        <a href="/wiki/File:Example.jpg" class="mw-file-description">
            <img src="//upload.wikimedia.org/thumb/e/330px-Example.jpg" />
        </a>
        <div class="thumbcaption">Seen from the <a href="/wiki/ISS">International Space Station</a> (details)</div>
    </div>
    """

    images = extract_images(html)

    assert images[0].caption == "Seen from the International Space Station (details)"


def test_magnify_link_does_not_pollute_caption():
    html = """
    <div class="thumb">
        <a href="/wiki/File:Example.jpg" class="mw-file-description">
            <img src="//upload.wikimedia.org/thumb/e/330px-Example.jpg" />
        </a>
        <div class="thumbcaption">
            <div class="magnify"><a href="/wiki/File:Example.jpg"> </a></div>
            Actual caption text
        </div>
    </div>
    """

    images = extract_images(html)

    assert images[0].caption == "Actual caption text"


def test_infobox_image_without_caption_row():
    html = """
    <table class="infobox">
        <tr>
            <td class="infobox-image">
                <a href="/wiki/File:Mountain.jpg" class="mw-file-description">
                    <img src="//upload.wikimedia.org/thumb/m/330px-Mountain.jpg" alt="" />
                </a>
            </td>
        </tr>
    </table>
    """

    images = extract_images(html)

    assert len(images) == 1
    assert images[0].caption is None
    assert images[0].alt is None


def test_infobox_image_with_caption_row():
    html = """
    <table class="infobox">
        <tr>
            <td class="infobox-image">
                <a href="/wiki/File:Mountain.jpg" class="mw-file-description">
                    <img src="//upload.wikimedia.org/thumb/m/330px-Mountain.jpg" />
                </a>
            </td>
        </tr>
        <tr>
            <td class="infobox-caption">Highest peak</td>
        </tr>
    </table>
    """

    images = extract_images(html)

    assert images[0].caption == "Highest peak"


def test_kartographer_maps_are_excluded():
    html = """
    <div class="thumb">
        <div class="mw-kartographer-map">
            <img src="//maps.wikimedia.org/map.png" />
        </div>
    </div>
    """

    assert extract_images(html) == []


def test_duplicate_images_are_removed():
    html = """
    <div class="thumb">
        <a href="/wiki/File:Same.jpg" class="mw-file-description">
            <img src="//upload.wikimedia.org/thumb/s/330px-Same.jpg" />
        </a>
        <div class="thumbcaption">First mention</div>
    </div>
    <div class="thumb">
        <a href="/wiki/File:Same.jpg" class="mw-file-description">
            <img src="//upload.wikimedia.org/thumb/s/220px-Same.jpg" />
        </a>
        <div class="thumbcaption">Second mention, different size</div>
    </div>
    """

    images = extract_images(html)

    assert len(images) == 1
    assert images[0].caption == "First mention"


def test_no_images_returns_empty_list():
    assert extract_images("<p>No images.</p>") == []


def test_empty_html_returns_empty_list():
    assert extract_images("") == []


def test_missing_src_is_skipped():
    html = """
    <div class="thumb">
        <img alt="no src attribute" />
    </div>
    """

    assert extract_images(html) == []