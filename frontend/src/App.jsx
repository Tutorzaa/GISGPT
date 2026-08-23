import { useEffect } from 'react'
import AOS from 'aos'
import 'aos/dist/aos.css'
import Magnet from './components/Magnet'
import GlareHover from './components/GlareHover'
import SpotlightCard from './components/SpotlightCard'
import Globe from './Globe'
import { site } from './content'
import './App.css'

const reducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

export default function App() {
  useEffect(() => {
    if (reducedMotion()) return
    AOS.init({ duration: 750, once: true, easing: 'ease-out-cubic', offset: 60 })
  }, [])

  return (
    <div className="landing">
      {/* ─────── Navbar ─────── */}
      <nav className="topbar">
        <a className="logo" href="/">
          <span className="logo-mark">🌍</span> {site.brand}
        </a>
        <div className="nav-links">
          {site.nav.map(n => (
            <a key={n.href} href={n.href}>
              {n.label}
            </a>
          ))}
        </div>
        <a className="nav-cta" href="/chat">
          เริ่มใช้งาน
        </a>
      </nav>

      {/* ─────── Hero ─────── */}
      <header className="hero">
        <div className="hero-copy">
          <span className="badge" data-aos="fade-up">
            {site.hero.badge}
          </span>
          <h1 data-aos="fade-up" data-aos-delay="80">
            {site.hero.title1}
            <br />
            <em>{site.hero.title2}</em>
          </h1>
          <p className="hero-sub" data-aos="fade-up" data-aos-delay="160">
            {site.hero.subtitle}
          </p>
          <div className="hero-actions" data-aos="fade-up" data-aos-delay="240">
            <Magnet padding={44} magnetStrength={2.2}>
              <a className="cta-link" href="/chat">
                <GlareHover
                  width="200px"
                  height="56px"
                  background="linear-gradient(135deg, #4f8cff 0%, #34d399 100%)"
                  borderRadius="14px"
                  borderColor="transparent"
                  glareColor="#ffffff"
                  glareOpacity={0.4}
                  glareSize={220}
                  transitionDuration={700}
                >
                  <span className="cta-label">{site.hero.ctaPrimary} →</span>
                </GlareHover>
              </a>
            </Magnet>
            <a className="btn-ghost" href="/dashboard">
              {site.hero.ctaSecondary}
            </a>
          </div>
          <p className="trust" data-aos="fade-up" data-aos-delay="320">
            {site.hero.trust}
          </p>
        </div>

        <div className="hero-visual" data-aos="zoom-in" data-aos-delay="150">
          <div className="globe-frame">
            <Globe />
          </div>
          <div className="chip chip-a">🛰️ Sentinel-2 · 10 m/px</div>
          <div className="chip chip-b">🌿 NDVI · NDWI · NDBI</div>
        </div>
      </header>

      {/* ─────── Features ─────── */}
      <section id="features" className="section">
        <div className="section-head" data-aos="fade-up">
          <h2>{site.featuresTitle}</h2>
          <p>{site.featuresSubtitle}</p>
        </div>
        <div className="feature-grid">
          {site.features.map((f, i) => (
            <div key={f.name} data-aos="fade-up" data-aos-delay={(i % 3) * 90}>
              <SpotlightCard
                className="card"
                spotlightColor="rgba(79, 140, 255, 0.18)"
              >
                <div className="card-icon">{f.icon}</div>
                <h3>{f.name}</h3>
                <p>{f.desc}</p>
              </SpotlightCard>
            </div>
          ))}
        </div>
      </section>

      {/* ─────── How it works ─────── */}
      <section id="how" className="section alt">
        <div className="section-head" data-aos="fade-up">
          <h2>{site.howTitle}</h2>
        </div>
        <ol className="steps">
          {site.howSteps.map((s, i) => (
            <li
              key={s.step}
              className="step"
              data-aos="fade-up"
              data-aos-delay={i * 110}
            >
              <span className="step-num">{s.step}</span>
              <h3>{s.name}</h3>
              <p>{s.desc}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ─────── Stats band ─────── */}
      <div className="stats-band" data-aos="fade-up">
        {site.stats.map(s => (
          <div key={s.label} className="stat">
            <strong>{s.value}</strong>
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      {/* ─────── Tech ─────── */}
      <section id="tech" className="section">
        <div className="section-head" data-aos="fade-up">
          <h2>{site.techTitle}</h2>
        </div>
        <div className="tech-chips" data-aos="fade-up" data-aos-delay="100">
          {site.techItems.map(t => (
            <span key={t} className="tchip">
              {t}
            </span>
          ))}
        </div>
      </section>

      {/* ─────── CTA banner ─────── */}
      <section className="cta-banner" data-aos="zoom-in">
        <h2>{site.ctaBanner.title}</h2>
        <p>{site.ctaBanner.subtitle}</p>
        <a href="/chat">{site.ctaBanner.button} →</a>
      </section>

      {/* ─────── Footer ─────── */}
      <footer className="footer">
        <div className="foot-grid">
          <div>
            <div className="logo foot-logo">
              <span className="logo-mark">🌍</span> {site.brand}
            </div>
            <p className="foot-tag">{site.footer.tagline}</p>
          </div>
          <div>
            <h4>ใช้งาน</h4>
            {site.footer.appLinks.map(l => (
              <a key={l.label} href={l.href}>
                {l.label}
              </a>
            ))}
          </div>
          <div>
            <h4>แหล่งข้อมูล</h4>
            {site.footer.dataLinks.map(l => (
              <a key={l.label} href={l.href} target="_blank" rel="noreferrer">
                {l.label}
              </a>
            ))}
          </div>
        </div>
        <div className="foot-credit">{site.footer.credit}</div>
      </footer>
    </div>
  )
}
