import { afterEach, expect, it } from 'vitest';
import { identityEvidenceHtml, reviewImageHtml, wireReviewPictures } from '../src/review-evidence';
afterEach(()=>{document.body.innerHTML='';});
it('身份候选区分来源资料与本地作品，全部作品与文件定位保留准确对象',()=>{
 document.body.innerHTML=identityEvidenceHtml({creator:'sample',babepedia_name:'Sample',videos:336,profile_url:'https://example.com/person',preview_assets:[{id:42,name:'sample.mp4'}]});
 expect(document.body.textContent).toContain('查看全部 336 部作品');
 expect(document.querySelector('[data-entity-name="sample"]')).not.toBeNull();
 expect(document.querySelector('[data-review-reveal="42"]')).not.toBeNull();
 expect(document.querySelector('[data-review-open-item="42"]')).not.toBeNull();
 expect(document.body.textContent).toContain('通过后记录身份判断');
 expect(document.querySelector('a')?.rel).toContain('noopener');
});
it('图片缺失与加载失败都保留同一个预览容器',()=>{
 document.body.innerHTML=reviewImageHtml();expect(document.querySelector('.reviewimageempty')?.hasAttribute('hidden')).toBe(false);
 document.body.innerHTML=reviewImageHtml('https://example.com/photo.jpg');wireReviewPictures(document);
 document.querySelector('img')!.dispatchEvent(new Event('error'));
 expect(document.querySelector<HTMLImageElement>('img')!.hidden).toBe(true);
 expect(document.querySelector<HTMLElement>('.reviewimageempty')!.hidden).toBe(false);
 expect(document.querySelectorAll('.reviewimage')).toHaveLength(1);
});
it('来源与名称按安全链接和文本处理，样本展示有界',()=>{
 document.body.innerHTML=identityEvidenceHtml({creator:'<script>',profile_url:'javascript:alert(1)',preview_assets:Array.from({length:60},(_,id)=>({id,name:'<b>sample</b>'}))});
 expect(document.querySelector('a')).toBeNull();expect(document.querySelector('script,b')).toBeNull();
 expect(document.querySelectorAll('[data-review-reveal]')).toHaveLength(6);
});
