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

def test_footnote_markers_are_excluded_from_body_caption():
    html = """
    <div class="thumb">
        <a href="/wiki/File:Bust.jpg" class="mw-file-description">
            <img src="//upload.wikimedia.org/thumb/b/330px-Bust.jpg" />
        </a>
        <div class="thumbcaption">The Tusculum portrait<sup class="reference"><a href="#cite_note-191">[191]</a></sup></div>
    </div>
    """

    images = extract_images(html)

    assert images[0].caption == "The Tusculum portrait"


def test_footnote_markers_are_excluded_from_infobox_caption():
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
            <td class="infobox-caption">Highest peak<sup class="reference"><a href="#cite_note-2">[2]</a></sup></td>
        </tr>
    </table>
    """

    images = extract_images(html)

    assert images[0].caption == "Highest peak"


# --- Новая разметка MediaWiki: <figure> + <figcaption> (сессия 2б) -------------


def _figure(file, caption, typeof="mw:File/Thumb", width=250):
    return f"""
    <figure class="mw-default-size" typeof="{typeof}">
        <a href="/wiki/File:{file}" class="mw-file-description">
            <img src="//thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/{file}/{width}px-{file}" class="mw-file-element" alt=""/>
        </a>
        <figcaption>{caption}</figcaption>
    </figure>
    """


def test_figure_illustration_is_extracted_with_figcaption():
    html = _figure("Bust.jpg", 'Bust of <a href="/wiki/Aristotle">Aristotle</a><sup class="reference"><a>[3]</a></sup>')

    images = extract_images(html)

    assert len(images) == 1
    assert images[0].caption == "Bust of Aristotle"
    assert images[0].thumbnail_url == "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Bust.jpg/250px-Bust.jpg"
    assert images[0].url == "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Bust.jpg/1280px-Bust.jpg"


def test_plain_file_figure_is_extracted():
    # typeof="mw:File" без Thumb: например, карта-схема в тексте (United States).
    images = extract_images(_figure("Map.png", "Map of states", typeof="mw:File"))

    assert [i.caption for i in images] == ["Map of states"]


def test_audio_and_video_figures_are_skipped():
    html = """
    <figure typeof="mw:File/Thumb"><span><audio class="mw-file-element" controls=""></audio></span><figcaption>Anthem</figcaption></figure>
    <figure typeof="mw:File/Thumb"><span><video class="mw-file-element" controls=""></video></span><figcaption>Film</figcaption></figure>
    """

    assert extract_images(html) == []


def test_figures_inside_tables_navboxes_and_service_boxes_are_skipped():
    html = (
        '<table class="wikitable"><tr><td>' + _figure("In_table.png", "x") + "</td></tr></table>"
        + '<div class="navbox">' + _figure("In_navbox.png", "x") + "</div>"
        + '<div class="side-box noprint">' + _figure("Listen.png", "Listen", typeof="mw:File") + "</div>"
        + _figure("Real.jpg", "Real illustration")
    )

    assert [i.caption for i in extract_images(html)] == ["Real illustration"]


def test_figure_in_infobox_is_not_duplicated_as_body_image():
    html = """
    <table class="infobox"><tr><td class="infobox-image">
    """ + _figure("Portrait.jpg", "Portrait", typeof="mw:File") + """
    </td></tr></table>
    """

    images = extract_images(html)

    assert len(images) == 1  # только как изображение инфобокса


def test_kartographer_figure_is_skipped():
    html = '<figure typeof="mw:File/Thumb"><div class="mw-kartographer-map"><img src="//maps.wikimedia.org/x.png"/></div><figcaption>Map</figcaption></figure>'

    assert extract_images(html) == []


def test_gallery_images_take_caption_from_gallerytext():
    html = """
    <ul class="gallery mw-gallery-packed">
      <li class="gallerybox">
        <div class="thumb"><span typeof="mw:File"><a href="/wiki/File:Stamp.jpg" class="mw-file-description"><img src="//thumb.wikimedia.org/x/120px-Stamp.jpg"/></a></span></div>
        <div class="gallerytext">Stamp of 2018</div>
      </li>
    </ul>
    """

    assert [i.caption for i in extract_images(html)] == ["Stamp of 2018"]


def test_figures_and_old_thumbs_keep_document_order():
    html = (
        _figure("First.jpg", "First")
        + """
        <div class="thumb tmulti"><div class="thumbinner">
            <a href="/wiki/File:Second.jpg" class="mw-file-description"><img src="//upload.wikimedia.org/thumb/s/220px-Second.jpg"/></a>
            <div class="thumbcaption">Second</div>
        </div></div>
        """
        + _figure("Third.jpg", "Third")
    )

    assert [i.caption for i in extract_images(html)] == ["First", "Second", "Third"]
