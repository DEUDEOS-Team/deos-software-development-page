# 🌐 DEOS Software Development Portal

Bu depo, **DEOS Otonom Araç Ekosistemi**'nin dağıtık yazılım mimarisini, Git alt modül ağacını, araç içi CAN-FD donanım topolojisini ve tüm alt modüllerin canlı GitHub commit geçmişini sunan resmi web portalıdır.

## 🚀 Canlı Portal
Web sitesine aşağıdaki bağlantıdan erişebilirsiniz:  
👉 **[https://deudeos-team.github.io/deos-software-development-page/](https://deudeos-team.github.io/deos-software-development-page/)**

---

## 🛠️ Mimari & Dosya Yapısı

* **`index.html`**: Mermaid.js şemasını, hover popover kartlarını ve alt sorumluluk tablosunu içeren tek sayfalık web uygulaması.
* **`responsibilities.json`**: Ekosistemdeki tüm modül ve alt sistemlerin **tek doğruluk kaynağı (Single Source of Truth)**. Hangi kutunun kime ait olduğu, bağlı repo, görev tanımı ve anlık `status_note` (Mevcut Durum) burada tutulur.
* **`commits.json`**: GitHub Actions otomasyonu tarafından oluşturulan ve ekosistemdeki 16+ deponun en güncel commit bilgilerini saklayan statik önbellek dosyasıdır (Ziyaretçilerin GitHub API kotasını tüketmesini engeller).
* **`scripts/fetch_commits.py`**: GitHub API üzerinden tüm depoların son commit hash, yazar, tarih ve mesajlarını toplayıp `commits.json` dosyasını oluşturan Python betiği.
* **`.github/workflows/update_commits.yml`**: Commit verilerini otomatik olarak güncelleyen GitHub Actions iş akışı.

---

## 🔄 Değişiklikler Sayfaya Nasıl Deploy Edilir?

Web portalı **GitHub Pages** üzerinde barınmaktadır. `main` dalına yapılan her `git push` işlemi sonrasında sayfa **otomatik olarak derlenir ve yayına alınır.**

### 1. Yeni Modül, Sorumluluk veya "Mevcut Durum" Güncellemesi
Eğer bir alt modülün sorumlusunu, açıklamasını, reposunu veya mevcut geliştirme durumunu (`status_note`) değiştirmek istiyorsanız:

1. `responsibilities.json` dosyasını açıp ilgili bileşeni güncelleyin:
   ```json
   {
     "id": "CORE",
     "title": "deos-core",
     "role_type": "Submodule (lib/deos_core)",
     "owner": "Emir Arkalı",
     "repo": "DEUDEOS-Team/deos-core",
     "path": null,
     "role": "Split-Horizon yönlendirici motoru, telemetri abonelikleri ve mandallanan arıza tablosu.",
     "status_note": "Çekirdek yapısı protokolden ayrıldı, geliştirmeler devam ediyor."
   }
   ```
2. Değişikliği commit edip `main` dalına pushlayın:
   ```bash
   git add responsibilities.json
   git commit -m "feat(arch): update deos-core status note"
   git push origin main
   ```
3. Push işlemi bittiğinde GitHub Actions hem commit önbelleğini yeniler hem de GitHub Pages yaklaşık **20-30 saniye içinde** canlı siteyi günceller.

> **💡 Not:** Eğer ana gömülü yazılım reposundaki (`deos_firmware/responsibilities.json`) dosyasında değişiklik yaptıysanız, dosyayı bu repoya kopyalayıp pushlamanız yeterlidir.

---

### 2. Arayüz & Tasarım Değişiklikleri (`index.html`)
Web arayüzünde (CSS, şema, popover kartları, tablo vb.) değişiklik yapmak için:

1. `index.html` dosyasını düzenleyin.
2. Değişiklikleri yerel ortamda test etmek için terminalden statik sunucu başlatabilirsiniz:
   ```bash
   python3 -m http.server 8000
   ```
   Tarayıcınızdan `http://localhost:8000` adresine giderek test edin.
3. Değişiklikleri commit edip pushlayın:
   ```bash
   git add index.html
   git commit -m "style(ui): improve popover layout and theme"
   git push origin main
   ```
4. GitHub Pages otomatik olarak devreye girip sayfayı günceller.

---

### 3. Canlı Commit Önbelleğini (`commits.json`) Güncelleme

Commit verileri iki farklı yolla güncel kalır:

#### A. Otomatik Güncelleme (15 Dakikada Bir)
* `.github/workflows/update_commits.yml` iş akışı her **15 dakikada bir** otomatik olarak çalışır.
* `GITHUB_TOKEN` (saatte 5.000 istek kotası) kullanarak depoları tarar ve yeni commit varsa `commits.json` dosyasını günceller.

#### B. Manuel Tetikleme (Tek Tıkla)
Eğer ekosistemdeki repolara yeni bir commit attıysanız ve 15 dakika beklemeden hemen sitede görmek istiyorsanız:
1. GitHub web arayüzünde deponun **Actions** sekmesine gidin.
2. Sol menüden **Update Ecosystem Commits** iş akışını seçin.
3. Sağ taraftaki **Run workflow** butonuna tıklayın.

#### C. Yerel Terminalden Güncelleme
İsterseniz yerel makinenizden de betiği çalıştırıp commit'i doğrudan pushlayabilirsiniz:
```bash
# GitHub CLI oturumunuz açıksa:
GITHUB_TOKEN=$(gh auth token) python3 scripts/fetch_commits.py

# Değişen commits.json dosyasını pushlayın:
git add commits.json
git commit -m "chore(data): refresh commit cache"
git push origin main
```

---

## ⚡ Hibrit Canlılık: Stale-While-Revalidate

* **0 ms Gecikme:** Ziyaretçiler siteye girdiğinde `commits.json` sayesinde sayfa anında açılır, hiçbir zaman *"Yükleniyor..."* beklemesi yaşanmaz.
* **Canlı Kontrol:** Sayfa açıldıktan sonra tarayıcı arka planda sessizce GitHub API'yi kontrol eder. Son birkaç dakika içinde yeni bir commit atılmışsa ekrandaki hash ve mesaj canlı olarak yenilenir.
* **Kota Koruması:** Kullanıcının GitHub API kotası dolsa dahi hiçbir hata verilmez; sistem statik `commits.json` verisiyle kusursuz şekilde çalışmaya devam eder.
