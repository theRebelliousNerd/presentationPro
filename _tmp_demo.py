import base64, io, requests
from PIL import Image, ImageDraw

base='http://localhost:18088'

# Prepare a screenshot
img = Image.new('RGB',(640,360),'white')
d = ImageDraw.Draw(img)
d.rectangle([40,40,600,100], fill='#333')
buf = io.BytesIO(); img.save(buf, format='PNG')
ss = 'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()

# Design: request a code layout with placement hints
req = {
  'slide': { 'title':'Demo Slide', 'content':['First','Second','Third'], 'screenshotDataUrl': ss },
  'theme': 'brand', 'pattern': 'grid', 'preferCode': True, 'preferLayout': True, 'variants': 1
}
r = requests.post(base+'/v1/slide/design', json=req)
print('design status', r.status_code)
out = r.json()
print('has placementCandidates:', 'placementCandidates' in out.get('designSpec',{}))

# Research: provide OCR image
img2 = Image.new('RGB',(500,150),'white')
d2 = ImageDraw.Draw(img2)
d2.rectangle([10,20,480,60], fill='#000')  # high-contrast band
buf2 = io.BytesIO(); img2.save(buf2, format='PNG')
ocr_img = 'data:image/png;base64,'+base64.b64encode(buf2.getvalue()).decode()

r2 = requests.post(base+'/v1/research/backgrounds', json={'query':'accessibility best practices', 'topK':3, 'imageDataUrl': ocr_img})
print('research status', r2.status_code)
print('has extractions:', 'extractions' in r2.json())
