import { Helmet } from 'react-helmet-async';

interface PageHeadProps {
    title?: string;
}

export const PageHead = ({ title }: PageHeadProps) => {
    const fullTitle = title ? `${title} | PSC Web` : 'PSC Web - 演劇制作管理システム';
    return (
        <Helmet>
            <title>{fullTitle}</title>
        </Helmet>
    );
};
