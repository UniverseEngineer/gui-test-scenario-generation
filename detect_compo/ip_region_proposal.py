import cv2
from os.path import join as pjoin
import time
import json
import numpy as np

import detect_compo.lib_ip.ip_preprocessing as pre
import detect_compo.lib_ip.ip_draw as draw
import detect_compo.lib_ip.ip_detection as det
import detect_compo.lib_ip.ip_segment as seg
import detect_compo.lib_ip.file_utils as file
import detect_compo.lib_ip.block_division as blk
import detect_compo.lib_ip.Component as Compo
from config.CONFIG_UIED import Config
C = Config()


# def processing_block(org, binary, blocks, block_pad):
#     image_shape = org.shape
#     uicompos_all = []
#     for block in blocks:
#         # *** Step 2.1 *** check: examine if the block is valid layout block
#         if block.block_is_top_or_bottom_bar(image_shape, C.THRESHOLD_TOP_BOTTOM_BAR):
#             continue
#         if block.block_is_uicompo(image_shape, C.THRESHOLD_COMPO_MAX_SCALE):
#             uicompos_all.append(block)
#
#         # *** Step 2.2 *** binary map processing: erase children block -> clipping -> remove lines(opt)
#         binary_copy = binary.copy()
#         for i in block.children:
#             blocks[i].block_erase_from_bin(binary_copy, block_pad)
#         block_clip_bin = block.compo_clipping(binary_copy)
#         # det.line_removal(block_clip_bin, show=True)
#
#         # *** Step 2.3 *** component extraction: detect components in block binmap -> convert position to relative
#         uicompos = det.component_detection(block_clip_bin)
#         Compo.cvt_compos_relative_pos(uicompos, block.bbox.col_min, block.bbox.row_min)
#         uicompos_all += uicompos
#     return uicompos_all


def nesting_inspection(org, grey, compos, ffl_block):
    '''
    Inspect all big compos through block division by flood-fill
    :param ffl_block: gradient threshold for flood-fill
    :return: nesting compos
    '''
    nesting_compos = []
    for i, compo in enumerate(compos):
        if compo.height > 50:
            replace = False
            clip_org = compo.compo_clipping(org)
            clip_grey = compo.compo_clipping(grey)
            n_compos = blk.block_division(clip_grey, org, grad_thresh=ffl_block, show=False)
            Compo.cvt_compos_relative_pos(n_compos, compo.bbox.col_min, compo.bbox.row_min)

            for n_compo in n_compos:
                if n_compo.redundant:
                    compos[i] = n_compo
                    replace = True
                    break
            if not replace:
                nesting_compos += n_compos
    return nesting_compos


def compo_detection(input_img_path, output_root, uied_params,
                    resize_by_height=600,
                    classifier=None, show=False, wai_key=0):

    start = time.perf_counter()
    name = input_img_path.split('/')[-1][:-4]
    ip_root = file.build_directory(pjoin(output_root, "ip"))

    # *** Step 1 *** pre-processing: read img -> get binary map
    org, grey = pre.read_img(input_img_path, resize_by_height)
    binary = pre.binarization(org, grad_min=int(uied_params['min-grad']), show=show, wait_key=wai_key)

    # *** Step 2 *** element detection
    det.rm_line(binary, show=show, wait_key=wai_key)
    # det.rm_line_v_h(binary, show=show)
    uicompos = det.component_detection(binary, min_obj_area=int(uied_params['min-ele-area']))
    # draw.draw_bounding_box(org, uicompos, show=show, name='components', wait_key=wai_key)

    # *** Step 3 *** results refinement
    uicompos = det.merge_intersected_corner(uicompos, org, is_merge_contained_ele=uied_params['merge-contained-ele'],
                                            max_gap=(0, 0), max_ele_height=25)
    Compo.compos_update(uicompos, org.shape)
    Compo.compos_containment(uicompos)
    # draw.draw_bounding_box(org, uicompos, show=show, name='merged', wait_key=wai_key)

    # *** Step 4 ** nesting inspection: treat the big compos as block and check if they have nesting element
    uicompos += nesting_inspection(org, grey, uicompos, ffl_block=uied_params['ffl-block'])
    uicompos = det.compo_filter(uicompos, min_area=int(uied_params['min-ele-area']))
    Compo.compos_update(uicompos, org.shape)
    draw.draw_bounding_box(org, uicompos, show=show, name='merged compo', write_path=pjoin(ip_root, 'result.jpg'), wait_key=wai_key)

    # *** Step 5 *** Image Inspection: recognize image -> remove noise in image -> binarize with larger threshold and reverse -> rectangular compo detection
    # if classifier is not None:
    #     classifier['Image'].predict(seg.clipping(org, uicompos), uicompos)
    #     draw.draw_bounding_box_class(org, uicompos, show=show)
    #     uicompos = det.rm_noise_in_large_img(uicompos, org)
    #     draw.draw_bounding_box_class(org, uicompos, show=show)
    #     det.detect_compos_in_img(uicompos, binary_org, org)
    #     draw.draw_bounding_box(org, uicompos, show=show)
    # if classifier is not None:
    #     classifier['Noise'].predict(seg.clipping(org, uicompos), uicompos)
    #     draw.draw_bounding_box_class(org, uicompos, show=show)
    #     uicompos = det.rm_noise_compos(uicompos)

    # *** Step 6 *** element classification: all category classification
    if classifier is not None:
        classifier['Elements'].predict(seg.clipping(org, uicompos), uicompos)
        draw.draw_bounding_box_class(org, uicompos, show=show, name='cls', write_path=pjoin(ip_root, 'result.jpg'))
        draw.draw_bounding_box_class(org, uicompos, write_path=pjoin(output_root, 'result.jpg'))

    Compo.compos_update(uicompos, org.shape)
    file.save_corners_json(pjoin(ip_root, name + '.json'), uicompos)
    file.save_corners_json(pjoin(output_root, 'compo.json'), uicompos)
    # seg.dissemble_clip_img_fill(pjoin(output_root, 'clips'), org, uicompos)

    print("[Compo Detection Completed in %.3f s] %s" % (time.perf_counter() - start, input_img_path))
    # if show:
    #     cv2.destroyAllWindows()
