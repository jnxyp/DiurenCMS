// 初始化Cropper实例
// Cropper实例全局变量名称为 cropper_{{ image_id }}
function avatar_edit_init(image_id, minAspectRatio, maxAspectRatio) {
    const image = $('#' + image_id)[0];
    const cropper = new Cropper(image, {
        viewMode:1,
        dragMode:'move',
        autoCropArea: 1.0,
        rotatable: false,
        scalable: false,
        minContainerHeight: 200,
        minContainerWidth: 0,
        responsive: true,
        preview: $('.' + image_id + '_preview'),
        crop: function (event) {
            $('#id_crop_x').val(event.detail.x);
            $('#id_crop_y').val(event.detail.y);
            $('#id_crop_width').val(event.detail.width);
            $('#id_crop_height').val(event.detail.height);
            console.log('233');
        },
        ready: function () {
            let cropper = this.cropper;
            let containerData = cropper.getContainerData();
            let cropBoxData = cropper.getCropBoxData();
            let aspectRatio = cropBoxData.width / cropBoxData.height;
            let newCropBoxWidth;

            if (aspectRatio < minAspectRatio || aspectRatio > maxAspectRatio) {
                newCropBoxWidth = cropBoxData.height * ((minAspectRatio + maxAspectRatio) / 2);

                cropper.setCropBoxData({
                    left: (containerData.width - newCropBoxWidth) / 2,
                    width: newCropBoxWidth
                });
            }
        },

        cropmove: function () {
            let cropper = this.cropper;
            let cropBoxData = cropper.getCropBoxData();
            let aspectRatio = cropBoxData.width / cropBoxData.height;

            if (aspectRatio < minAspectRatio) {
                cropper.setCropBoxData({
                    width: cropBoxData.height * minAspectRatio
                });
            } else if (aspectRatio > maxAspectRatio) {
                cropper.setCropBoxData({
                    width: cropBoxData.height * maxAspectRatio
                });
            }
        },
    });
    // 将比例写入Cropper实例
    cropper.minAspectRatio = minAspectRatio;
    cropper.maxAspectRatio = maxAspectRatio;
    // 将Cropper对象写入全局作用域
    window['cropper' + '_' + image_id] = cropper
}

// 调用此方法来手动调整选区比例
function adjust_ratio(cropper) {
    let cropBoxData = cropper.getCropBoxData();
    let aspectRatio = cropBoxData.width / cropBoxData.height;

    if (aspectRatio < cropper.minAspectRatio) {
        cropper.setCropBoxData({
            width: cropBoxData.height * cropper.minAspectRatio
        });
    } else if (aspectRatio > cropper.maxAspectRatio) {
        cropper.setCropBoxData({
            width: cropBoxData.height * cropper.maxAspectRatio
        });
    }
}
