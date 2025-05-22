// 图片切换功能
let currentImageIndex = 0;

function getThumbnailSrcArray() {
    const thumbnails = document.querySelectorAll('.thumbnail-container img');
    return Array.from(thumbnails).map(img => img.src);
}
const images = getThumbnailSrcArray()

function changeImage(src) {
    document.getElementById('mainImage').src = src;
    
    // 更新缩略图激活状态
    const thumbnails = document.querySelectorAll('.thumbnail');
    thumbnails.forEach((thumb, index) => {
        if (thumb.querySelector('img').src.includes(src)) {
            thumb.classList.add('active');
            currentImageIndex = index;
        } else {
            thumb.classList.remove('active');
        }
    });
}

function prevImage() {
    currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
    changeImage(images[currentImageIndex]);
}

function nextImage() {
    currentImageIndex = (currentImageIndex + 1) % images.length;
    changeImage(images[currentImageIndex]);
}

// 自动轮播
let slideInterval = setInterval(nextImage, 3000);

// 鼠标悬停时暂停自动轮播
document.querySelector('.product-gallery').addEventListener('mouseenter', () => {
    clearInterval(slideInterval);
});

document.querySelector('.product-gallery').addEventListener('mouseleave', () => {
    slideInterval = setInterval(nextImage, 3000);
});

// 颜色选择
const colorOptions = document.querySelectorAll('.color-option');
colorOptions.forEach(option => {
    option.addEventListener('click', function() {
        colorOptions.forEach(opt => opt.classList.remove('active'));
        this.classList.add('active');
    });
});

// 数量增减
const decreaseBtn = document.querySelector('.decrease');
const increaseBtn = document.querySelector('.increase');
const quantityInput = document.querySelector('.quantity-control input');

decreaseBtn.addEventListener('click', () => {
    let value = parseInt(quantityInput.value);
    if (value > 1) {
        quantityInput.value = value - 1;
    }
});

increaseBtn.addEventListener('click', () => {
    let value = parseInt(quantityInput.value);
    quantityInput.value = value + 1;
});

// 按钮点击效果
const addToCartBtn = document.querySelector('.add-to-cart');
const buyNowBtn = document.querySelector('.buy-now');

addToCartBtn.addEventListener('click', () => {
    alert('商品已添加到购物车！');
});

buyNowBtn.addEventListener('click', () => {
    alert('即将跳转到结算页面！');
});