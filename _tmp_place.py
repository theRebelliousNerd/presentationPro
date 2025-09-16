import base64, io, requests
from PIL import Image, ImageDraw
base='http://localhost:18088'
img = Image.new('RGB',(640,360),'white')
d = ImageDraw.Draw(img)
d.rectangle([40,40,600,100], fill='#333')
buf = io.BytesIO(); img.save(buf, format='PNG')
ss = 'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
r = requests.post(base+'/v1/visioncv/placement', json={'screenshotDataUrl': ss})
print(r.status_code)
print(list(r.json().keys()))
print(len(r.json().get('candidates',[])))
