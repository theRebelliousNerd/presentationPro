import base64, io, requests
from PIL import Image, ImageDraw
base='http://localhost:18088'
img = Image.new('RGB',(640,360),'white')
d = ImageDraw.Draw(img)
d.rectangle([40,40,600,100], fill='#333')
buf = io.BytesIO(); img.save(buf, format='PNG')
ss = 'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()

req = {
  'slide': { 'title':'Demo Slide', 'content':['First','Second','Third'], 'screenshotDataUrl': ss },
  'theme': 'brand', 'pattern': 'grid', 'preferCode': True, 'preferLayout': True, 'variants': 1
}
r = requests.post(base+'/v1/slide/design', json=req)
print(r.status_code)
print('keys', list(r.json().keys()))
print('designSpec keys', list(r.json().get('designSpec',{}).keys()))
print(r.text)
