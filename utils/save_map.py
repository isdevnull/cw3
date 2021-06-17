import io
import os
from PIL import Image

def save_map_html_and_png(m, filename: str, html_dir: str='html', imgs_dir: str='imgs', delay: int=5):
    if not os.path.exists(html_dir):
        os.makedirs(html_dir)
    m.save('{dir}/{name}.html'.format(dir=html_dir, name=filename)) # save as html

    img_data = m._to_png(delay)
    img = Image.open(io.BytesIO(img_data))
    img.save('{dir}/{name}.png'.format(dir=imgs_dir, name=filename)) # save as png
