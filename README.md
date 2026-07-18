# FleetCar - Filo Kiralama & Yönetim Uygulaması

FleetCar, şirketlerin araç kiralama teklifleri alabileceği, teklif onaylandıktan sonra ise araçların bakım, lastik, yol yardım ve ikame araç gibi operasyonel süreçlerini yönetebileceği modern bir filo yönetim platformudur.

Proje iki ana bölümden oluşmaktadır:
1. **Backend**: Python (FastAPI) bellek içi veri yapısı.
2. **Frontend**: Vue.js 3 (Vite, Vue Router, modern aydınlık tema).

---

## Projeyi Çalıştırma

### 1. Backend'i Çalıştırma
Gerekli bağımlılıkları yükleyin ve Uvicorn sunucusunu başlatın:
```bash
cd backend
# Sanal ortamı aktive edin (MacOS/Linux)
source venv/bin/activate
# Bağımlılıkları yükleyin
pip install -r requirements.txt
# Sunucuyu başlatın
uvicorn app.main:app --port 8000 --reload
```
API dokümantasyonuna [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) adresinden erişebilirsiniz.

### 2. Frontend'i Çalıştırma
Bağımlılıkları yükleyin ve Vite geliştirme sunucusunu çalıştırın:
```bash
cd frontend
npm install
npm run dev
```
Uygulamaya tarayıcınızda [http://localhost:5173](http://localhost:5173) adresinden erişebilirsiniz.

---

## Giriş Bilgileri (Geliştirme Ortamı)

* **Müşteri Portalı Giriş**:
  - Şifre: `admin123` (Anasayfada teklif motoru doldurulduktan sonra otomatik tanımlanır).
* **FleetCar Yönetici Portalı Giriş (`/admin-login`)**:
  - Kullanıcı Adı: Herhangi bir kullanıcı adı
  - Şifre: `django123` (Django entegrasyonu öncesi geçici test şifresi).

---

## Django Yönetici (Admin) Kimlik Doğrulama Entegrasyon Kılavuzu

Yönetici arayüzünde (`/admin-portal`) oturum açan FleetCar yöneticilerinin bilgilerini yönetmek ve doğrulamak için bir Django backend entegrasyonu kurmak oldukça pratiktir. Aşağıdaki adımları takip ederek Django ile kimlik doğrulama API'sini ayağa kaldırabilir ve Vue.js frontend'ine bağlayabilirsiniz.

### 1. Django ve Django REST Framework Kurulumu
Yeni bir Python ortamında Django ve API geliştirmeyi kolaylaştıran REST Framework kütüphanesini kurun:
```bash
pip install django djangorestframework django-cors-headers
```

### 2. Django Projesi ve Uygulaması Oluşturma
```bash
django-admin startproject fleetcar_admin .
python manage.py startapp authentication
```

### 3. Settings Ayarları (`settings.py`)
`INSTALLED_APPS` ve middleware listesine gerekli kütüphaneleri ekleyin:
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework.authtoken', # Token tabanlı auth için
    'corsheaders',
    'authentication',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # CORS izinleri için en üstte olmalı
    ...
]

# CORS İzinleri (Vue development sunucusu için)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# REST Framework Kimlik Doğrulama Ayarları
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

### 4. Admin Kullanıcısı (Superuser) Oluşturma
Veritabanını migrate edin ve Django yönetim paneline giriş için ilk yöneticiyi oluşturun:
```bash
python manage.py migrate
python manage.py createsuperuser
# Sizden kullanıcı adı, e-posta ve şifre isteyecektir. (Örn: admin / django123)
```
Django admin paneline artık `http://127.0.0.1:8000/admin` adresinden erişerek diğer yönetici kullanıcılarını veya şirket yöneticilerini manuel olarak ekleyebilirsiniz.

### 5. Login API Uç Noktası Oluşturma (`authentication/views.py`)
Kullanıcı adı ve şifreyi doğrulayıp benzersiz bir token dönen API görünümü:
```python
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username
        })
```

`urls.py` dosyanıza bu route'u ekleyin:
```python
from django.urls import path
from authentication.views import CustomObtainAuthToken

urlpatterns = [
    path('api/admin/login/', CustomObtainAuthToken.as_view(), name='admin_login'),
]
```

### 6. Vue.js Frontend Bağlantısı (`AdminLoginView.vue`)
Frontend tarafındaki mock login fonksiyonunu (`handleLogin`), Django sunucunuza HTTP POST isteği atacak şekilde aşağıdaki gibi güncelleyin:

```javascript
// frontend/src/views/AdminLoginView.vue içindeki script kısmı güncellemesi:
const handleLogin = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/admin/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })

    if (response.ok) {
      const data = await response.json()
      // Django'dan dönen token'ı kaydediyoruz
      localStorage.setItem('fleetcar_admin_token', data.token)
      localStorage.setItem('fleetcar_admin_user', data.username)
      router.push('/admin-portal')
    } else {
      alert('Hatalı kullanıcı adı veya şifre!')
    }
  } catch (error) {
    console.error('Django Auth Connection Error:', error)
    alert('Django backend sunucusuna bağlanılamadı.')
  }
}
```

Bu yapı sayesinde yöneticilerin oturum yönetimi tamamen Django'nun güvenli `User` modeli ve REST token yapısıyla yönetilmiş olur.
