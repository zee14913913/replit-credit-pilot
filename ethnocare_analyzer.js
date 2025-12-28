// ============================================
// Ethnocare 网站分析脚本
// 使用方法：在 ethnocare.ca 的浏览器控制台运行此脚本
// ============================================

console.log('🔍 开始分析 Ethnocare 网站...\n');

// 1. 分析滚动动画库
console.log('📊 1. 滚动动画库检测:');
const scrollLibraries = {
    'GSAP': window.gsap,
    'ScrollTrigger': window.ScrollTrigger,
    'Locomotive Scroll': window.LocomotiveScroll,
    'Lenis': window.lenis || window.Lenis,
    'ScrollMagic': window.ScrollMagic,
    'AOS': window.AOS
};

Object.entries(scrollLibraries).forEach(([name, lib]) => {
    if (lib) {
        console.log(`   ✅ ${name} - 已检测到`);
    }
});

// 2. 检测 3D 库
console.log('\n🎨 2. 3D/动画库检测:');
const threeDLibs = {
    'Three.js': window.THREE,
    'WebGL': document.querySelector('canvas'),
    'Lottie': window.lottie,
    'PixiJS': window.PIXI
};

Object.entries(threeDLibs).forEach(([name, lib]) => {
    if (lib) {
        console.log(`   ✅ ${name} - 已检测到`);
        if (name === 'WebGL' && lib) {
            console.log(`      Canvas 元素: ${lib.tagName} (${lib.width}x${lib.height})`);
        }
    }
});

// 3. 分析 CSS 动画和过渡
console.log('\n✨ 3. CSS 动画分析:');
const animatedElements = document.querySelectorAll('[class*="animate"], [data-aos], [data-scroll]');
console.log(`   发现 ${animatedElements.length} 个带动画的元素`);

if (animatedElements.length > 0) {
    const sample = animatedElements[0];
    const computed = window.getComputedStyle(sample);
    console.log('   示例元素样式:');
    console.log(`   - transform: ${computed.transform}`);
    console.log(`   - transition: ${computed.transition}`);
    console.log(`   - animation: ${computed.animation}`);
}

// 4. 检测滚动行为
console.log('\n🎢 4. 滚动配置:');
const scrollContainer = document.querySelector('[data-scroll-container]') || 
                       document.querySelector('.smooth-scroll') ||
                       document.documentElement;
const scrollStyle = window.getComputedStyle(scrollContainer);
console.log(`   scroll-behavior: ${scrollStyle.scrollBehavior}`);
console.log(`   overflow: ${scrollStyle.overflow}`);

// 5. 检测视差效果
console.log('\n🌊 5. 视差效果检测:');
const parallaxElements = document.querySelectorAll('[data-speed], [data-parallax], .parallax');
console.log(`   发现 ${parallaxElements.length} 个视差元素`);
parallaxElements.forEach((el, i) => {
    if (i < 3) { // 只显示前3个
        console.log(`   - ${el.tagName}.${el.className}: speed=${el.dataset.speed || '未设置'}`);
    }
});

// 6. 分析页面加载动画
console.log('\n⏳ 6. 页面加载动画:');
const preloader = document.querySelector('[class*="preloader"], [class*="loader"]');
if (preloader) {
    console.log(`   ✅ 检测到预加载器: ${preloader.className}`);
    const preloaderStyle = window.getComputedStyle(preloader);
    console.log(`   - opacity: ${preloaderStyle.opacity}`);
    console.log(`   - transition: ${preloaderStyle.transition}`);
}

// 7. 提取关键 CSS 变量
console.log('\n🎨 7. CSS 自定义属性:');
const rootStyles = window.getComputedStyle(document.documentElement);
const cssVars = [
    '--color-text',
    '--color-background',
    '--color-accent',
    '--spacing-large',
    '--spacing-huge',
    '--header-height',
    '--border-radius'
];

cssVars.forEach(varName => {
    const value = rootStyles.getPropertyValue(varName);
    if (value) {
        console.log(`   ${varName}: ${value.trim()}`);
    }
});

// 8. 检测缓动函数
console.log('\n📈 8. 缓动函数 (Easing):');
const elements = document.querySelectorAll('*');
const easings = new Set();
elements.forEach(el => {
    const style = window.getComputedStyle(el);
    const transition = style.transitionTimingFunction;
    if (transition && transition !== 'ease') {
        easings.add(transition);
    }
});

if (easings.size > 0) {
    console.log('   检测到的缓动函数:');
    easings.forEach(easing => console.log(`   - ${easing}`));
}

// 9. 分析关键帧动画
console.log('\n🎬 9. CSS 关键帧动画:');
try {
    const styleSheets = Array.from(document.styleSheets);
    const keyframeNames = new Set();
    
    styleSheets.forEach(sheet => {
        try {
            const rules = Array.from(sheet.cssRules || []);
            rules.forEach(rule => {
                if (rule.type === CSSRule.KEYFRAMES_RULE) {
                    keyframeNames.add(rule.name);
                }
            });
        } catch (e) {
            // 跨域样式表无法访问
        }
    });
    
    console.log(`   发现 ${keyframeNames.size} 个关键帧动画:`);
    Array.from(keyframeNames).slice(0, 10).forEach(name => {
        console.log(`   - @keyframes ${name}`);
    });
} catch (e) {
    console.log('   无法访问样式表 (可能是跨域限制)');
}

// 10. 提取 JavaScript 配置
console.log('\n⚙️ 10. JavaScript 配置:');
console.log('   window 对象上的动画相关属性:');
['gsap', 'ScrollTrigger', 'lenis', 'Lenis', 'locomotive'].forEach(prop => {
    if (window[prop]) {
        console.log(`   ✅ window.${prop} 存在`);
        if (typeof window[prop] === 'object') {
            console.log(`      类型: ${window[prop].constructor.name}`);
        }
    }
});

// 11. 检测 Intersection Observer
console.log('\n👁️ 11. Intersection Observer:');
const hasIntersectionObserver = 'IntersectionObserver' in window;
console.log(`   ${hasIntersectionObserver ? '✅' : '❌'} Intersection Observer API`);

// 12. 页面性能指标
console.log('\n⚡ 12. 性能指标:');
if (window.performance && window.performance.timing) {
    const timing = window.performance.timing;
    const loadTime = timing.loadEventEnd - timing.navigationStart;
    const domReady = timing.domContentLoadedEventEnd - timing.navigationStart;
    console.log(`   页面加载时间: ${loadTime}ms`);
    console.log(`   DOM 准备时间: ${domReady}ms`);
}

// 13. 检测特殊效果
console.log('\n✨ 13. 特殊效果检测:');
const effects = {
    '模糊效果': document.querySelectorAll('[style*="blur"]').length,
    '渐变': document.querySelectorAll('[style*="gradient"]').length,
    '阴影': document.querySelectorAll('[style*="shadow"]').length,
    '变换': document.querySelectorAll('[style*="transform"]').length,
    '混合模式': document.querySelectorAll('[style*="mix-blend-mode"]').length
};

Object.entries(effects).forEach(([name, count]) => {
    if (count > 0) {
        console.log(`   ${name}: ${count} 个元素`);
    }
});

// 14. 总结建议
console.log('\n\n📋 ============ 总结建议 ============\n');
console.log('要实现类似 Ethnocare 的流畅动画效果，需要:');
console.log('');
console.log('1️⃣  安装核心库:');
console.log('   npm install gsap @studio-freight/lenis');
console.log('');
console.log('2️⃣  实现平滑滚动:');
console.log('   - 使用 Lenis 或 Locomotive Scroll');
console.log('   - 配置 easing: cubic-bezier(0.165, 0.84, 0.44, 1)');
console.log('');
console.log('3️⃣  添加滚动触发动画:');
console.log('   - GSAP ScrollTrigger');
console.log('   - 视差效果 (data-speed 属性)');
console.log('');
console.log('4️⃣  优化性能:');
console.log('   - 使用 transform 和 opacity (GPU 加速)');
console.log('   - will-change 属性');
console.log('   - requestAnimationFrame');
console.log('');
console.log('5️⃣  添加页面加载动画:');
console.log('   - Preloader 组件');
console.log('   - 淡入淡出效果');
console.log('');
console.log('====================================\n');

console.log('✅ 分析完成！请查看上述输出。');
