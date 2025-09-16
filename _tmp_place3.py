import base64, io, requests
from PIL import Image, ImageDraw
base='http://localhost:18088'
img=Image.new('RGB',(640,360),'white')
d=ImageDraw.Draw(img)
d.rectangle([40,40,600,100], fill='#333')
b=io.BytesIO(); img.save(b, format='PNG')
ss='data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
res=requests.post(base+'/v1/visioncv/placement', json={'screenshotDataUrl': ss})
print(res.status_code)
print(list(res.json().keys()))
print(len(res.json().get('candidates',[])))
