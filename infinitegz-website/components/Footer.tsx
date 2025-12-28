'use client'

import Link from 'next/link'
import { useLanguage } from '@/contexts/LanguageContext'

export default function Footer() {
  const { t } = useLanguage()
  
  return (
    <footer id="contact" className="relative w-full overflow-hidden min-h-screen flex items-center">
      {/* 顶部激光分隔线 */}
      <div className="absolute top-0 left-0 right-0">
        <div className="laser-divider"></div>
      </div>
      {/* 背景图片占位 */}
      <div className="absolute inset-0">
        <div 
          className="h-full w-full" 
          style={{
            backgroundImage: 'none',
            backgroundSize: 'cover',
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'bottom',
            opacity: 0
          }}
        />
      </div>

      {/* Footer 内容 */}
      <section className="py-16 sm:py-32 w-full">
        <div className="mx-auto w-full px-4 lg:px-6 xl:max-w-7xl space-y-16 sm:space-y-32">
          {/* CTA 区域 */}
          <div className="text-center space-y-8">
            <h2 className="text-3xl md:text-4xl lg:text-5xl tracking-tight text-primary">
              {t.home.footer.title}
            </h2>
            <p className="text-secondary text-base md:text-lg max-w-2xl mx-auto">
              {t.home.footer.description}
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
              <Link href="https://portal.infinitegz.com" className="btn-xai btn-xai-primary">
                {t.common.getStarted}
              </Link>
              <Link href="https://wa.me/60123456789" target="_blank" className="btn-xai">
                {t.common.whatsappUs}
              </Link>
            </div>
          </div>

          {/* 链接网格 */}
          <div className="relative grid gap-16 md:grid-cols-4">
            {/* Try CreditPilot On */}
            <div>
              <div className="space-y-5">
                <div>
                  <span className="mono-tag text-sm">{t.home.footer.sections.try}</span>
                </div>
                <div>
                  <Link href="https://portal.infinitegz.com" target="_blank" className="hover:underline">
                    {t.home.footer.links.web}
                  </Link>
                </div>
                <div>
                  <Link href="https://wa.me/60123456789" target="_blank" className="hover:underline">
                    {t.home.footer.links.whatsapp}
                  </Link>
                </div>
                <div>
                  <Link href="tel:+60123456789" className="hover:underline">
                    {t.home.footer.links.phone}
                  </Link>
                </div>
              </div>
            </div>

            {/* Products */}
            <div>
              <div className="space-y-5">
                <div>
                  <span className="mono-tag text-sm">{t.home.footer.sections.products}</span>
                </div>
                <div>
                  <Link href="#products" className="hover:underline">
                    {t.home.footer.links.creditpilot}
                  </Link>
                </div>
                <div>
                  <Link href="#products" className="hover:underline">
                    {t.home.footer.links.advisory}
                  </Link>
                </div>
                <div>
                  <Link href="#products" className="hover:underline">
                    {t.home.footer.links.creditCard}
                  </Link>
                </div>
                <div>
                  <Link href="#products" className="hover:underline">
                    {t.home.footer.links.digital}
                  </Link>
                </div>
                <div>
                  <Link href="#products" className="hover:underline">
                    {t.home.footer.links.accounting}
                  </Link>
                </div>
              </div>
            </div>

            {/* Company */}
            <div>
              <div className="space-y-5">
                <div>
                  <span className="mono-tag text-sm">{t.home.footer.sections.company}</span>
                </div>
                <div>
                  <Link href="#company" className="hover:underline">
                    {t.home.footer.links.about}
                  </Link>
                </div>
                <div>
                  <Link href="#company" className="hover:underline">
                    {t.home.footer.links.careers}
                  </Link>
                </div>
                <div>
                  <Link href="#contact" className="hover:underline">
                    {t.home.footer.links.contact}
                  </Link>
                </div>
                <div>
                  <Link href="#resources" className="hover:underline">
                    {t.home.footer.links.newsUpdates}
                  </Link>
                </div>
                <div>
                  <Link href="#company" className="hover:underline">
                    {t.home.footer.links.partners}
                  </Link>
                </div>
              </div>
            </div>

            {/* Resources */}
            <div>
              <div className="space-y-5">
                <div>
                  <span className="mono-tag text-sm">{t.home.footer.sections.resources}</span>
                </div>
                <div>
                  <Link href="/dsr-guide" className="hover:underline">
                    {t.home.footer.links.dsrGuide}
                  </Link>
                </div>
                <div>
                  <Link href="/tax-tips" className="hover:underline">
                    {t.home.footer.links.taxOptimization}
                  </Link>
                </div>
                <div>
                  <Link href="/faq" className="hover:underline">
                    {t.home.footer.links.faq}
                  </Link>
                </div>
                <div>
                  <Link href="/privacy" className="hover:underline">
                    {t.home.footer.links.privacy}
                  </Link>
                </div>
                <div>
                  <Link href="/legal" className="hover:underline">
                    {t.home.footer.links.legal}
                  </Link>
                </div>
              </div>
            </div>
          </div>
          
          {/* 底部版权信息 */}
          <div className="pt-16 border-t border-primary/10">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-secondary">
              <p>{t.home.footer.copyright}</p>
              <div className="flex gap-6">
                <Link href="/privacy" className="hover:text-primary transition-colors">
                  {t.home.footer.links.privacy}
                </Link>
                <Link href="/terms" className="hover:text-primary transition-colors">
                  {t.home.footer.links.terms}
                </Link>
                <Link href="/legal" className="hover:text-primary transition-colors">
                  {t.home.footer.links.legal}
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </footer>
  )
}
